# SIH26153 — Prediction, ATT&CK Mapping & Explainability Audit

**Audit Date:** 2026-09-21

---

## Inference Pipeline Walk-Through

End-to-end trace from uploaded file to outputs:

```
1. User uploads CSV/PCAP (app.py:393-414)
2. TrafficParser.parse_csv() or parse_pcap() (parser.py:48-193)
   - Column standardisation and default-filling
3. TrafficParser.create_time_windows() (parser.py:195-332)
   - 10-second windows → DataFrame with 25 FEATURE_COLUMNS
4. WorldModelForecaster.predict_k_steps(df_win_sub, K) (world_model.py:162-217)
   - Normalise: X_scaled = (X - mean_) / scale_
   - Build seq_buffer: last history_len=4 windows
   - Autoregressive loop K times: LSTM → pred_state, pred_risk
   - Returns {risk_trajectory: [float×K], forecast_df: DataFrame[K rows]}
5. RuleBasedMITREMapper.map_state_to_stage(current_state) (world_model.py:246-270)
   - Applies 12 rule thresholds to current state dict
   - Returns {name, id, technique, confidence}
6. RuleBasedMITREMapper.map_state_to_stage(future_state) (app.py:482)
   - Same call on last forecasted state from df_forecast.iloc[-1]
7. SOCRiskPrioritizer.calculate_prioritized_risk() (world_model.py:300-350)
   - Composite score = peak_risk × (asset_weight/2.5) × (stage_weight/2.5)
8. AttackExplainer.explain_window() (explainer.py:56-112)
   - GradientShap.attribute() with 50 samples against background sequences
   - Returns top-10 features with per-timestep attribution
```

### Train/Serve Skew Analysis

| Aspect | Training | Inference | Skew? |
|---|---|---|---|
| Scaler source | `train.py:102-105`: fit on train split | `app.py:314-316`: loaded from `scaler.pkl`, then re-applied over model's internal mean_/scale_ | ⚠️ Double-application risk: `WorldModelForecaster.load_model()` loads `mean_`/`scale_` from `.pth`, then `app.py` overwrites them with `scaler.pkl`. Both should be identical if from same training run, but the mechanism is fragile. |
| Feature order | `FEATURE_COLUMNS` constant | Same constant imported | ✅ |
| Window size | 10.0 seconds | 10.0 seconds | ✅ |
| History length | 4 | 4 (loaded from checkpoint) | ✅ |
| Normalisation formula | `(X - mean_) / scale_` | `(X - mean_) / scale_` | ✅ |

---

## Output Contract Review (R12, R13, R14)

### R12: Infiltration Probability Time-Series

| Output | Present | Location |
|---|---|---|
| K probability values | ✅ | `risk_trajectory` list, `world_model.py:215` |
| Displayed as timeline chart | ✅ | `app.py:550-592` (Plotly scatter) |
| Connects to alert threshold | ✅ | `app.py:594-597` conditional warning |
| Uncertainty estimate | ❌ | Only point predictions, no confidence interval |

### R13: Predicted ATT&CK Stage

| Output | Present | Location | Notes |
|---|---|---|---|
| Stage name | ✅ | `mitre_info['name']` | Both current and future state |
| MITRE ID | ✅ | `mitre_info['id']` | Tactic IDs (TA00XX) |
| Technique | ✅ | `mitre_info['technique']` | Technique IDs (T1XXX) |
| From forecasted state | ⚠️ Partial | `app.py:482`: `future_mitre_info = RuleBasedMITREMapper.map_state_to_stage(future_state_dict)` where `future_state_dict = df_forecast.iloc[-1].to_dict()` — IS the K-step forecasted state | The stage is technically derived from forecasted state, but the mapping is rule-based |
| Confidence score | ⚠️ Hard-coded | `confidence` values are fixed per rule match (0.95, 0.85, 0.75, etc.) `world_model.py:259-263` | Not probabilistic |

### R14: Feature Attribution

| Output | Present | Location | Notes |
|---|---|---|---|
| Attribution method | ✅ Captum GradientShap | `explainer.py:3,32` | |
| Per-sample | ✅ | Called fresh per window | |
| Per-timestep | ✅ | `attr_matrix` shape (history_len, n_features) | |
| Named features | ✅ | `FEATURE_COLUMNS` names | |
| Top-10 returned | ✅ | `explainer.py:102` | |
| Natural language narrative | ✅ | `explainer.py:114-140` | Template-based but readable |
| Applied to deployed model | ✅ | `AttackExplainer(model=forecaster.model...)` | Same model used for inference |
| Sanity check (top feature removal) | ❌ Not implemented | — | Test suite checks `total_shap != 0` but not feature-removal impact |

---

## ATT&CK Mapping Table

| Dataset Label (CIC-IDS-2018) | Mapped Stage | Tactic ID | Technique ID | How Derived | Confidence | Honestly Supported? |
|---|---|---|---|---|---|---|
| BENIGN | Benign | TA0000 | Normal Traffic | Rule: all scores = 0.05 (Benign wins) | 20% | ✅ |
| SSH-BruteForce / FTP-BruteForce | Initial Access | TA0001 | T1110 Brute Force | Rule: syn_ratio > 0.3 AND bytes_pkt > 300 | 60% | ⚠️ Plausible but heuristic |
| PortScan | Reconnaissance | TA0043 | T1046 Net Service Scan | Rule: port_scan_score > 3.0 OR (syn_ratio > 0.5 AND bytes_pkt < 150) | 40% | ✅ Good heuristic |
| DoS / DDoS | Initial Access or Reconnaissance | TA0001/TA0043 | T1190 / T1046 | Rule-based on SYN ratio and byte volume | Variable | ⚠️ DDoS does not map cleanly to a kill-chain stage |
| Bot (C2 beaconing) | Command & Control | TA0011 | T1071 App Protocol C2 | Rule: iat_variance < 0.005 AND unique_dsts ≤ 2 AND tot_bytes > 1000 | 85% | ✅ Good signature |
| Infiltration | Lateral Movement / Exfiltration | TA0008/TA0010 | T1021/T1041 | Rule: unique_dsts ≥ 3 OR high byte volume | Variable | ⚠️ Ambiguous mapping |
| Web Attacks | Initial Access | TA0001 | T1190 Exploit Public App | Rule: syn_ratio + bytes heuristic | 60% | ⚠️ Web attack != always T1190 |

### Which of the 5 Required Stages Are Actually Supported?

| Stage | Supported? | Evidence | Notes |
|---|---|---|---|
| Reconnaissance | ✅ Yes | Rule in mapper for port_scan_score and SYN probe heuristic | PortScan in CIC-IDS maps cleanly |
| Initial Access | ✅ Yes | Rule for brute force / exploit payload signatures | SSH-BruteForce, FTP-BruteForce, Web Attacks |
| Lateral Movement | ✅ Yes | Rule for high unique_dsts + high_port_ratio | Infiltration label in CIC-IDS |
| Command & Control | ✅ Yes | Rule for low IAT variance (beaconing) | Bot label in CIC-IDS |
| Exfiltration | ✅ Yes | Rule for very high bytes/packet and total bytes | Infiltration (exfil phase) in CIC-IDS |

All 5 stages supported. However, the mapping is rule-based — no learned stage classifier. The stage confidence values are hard-coded constants, not probabilities.

**Gap:** Stage labels are never evaluated quantitatively. A stage accuracy metric (% correct stage classification on labeled windows) is missing.

---

## Explainability Method Review

### Captum GradientShap Configuration

| Parameter | Value | Location |
|---|---|---|
| Attribution method | `GradientShap` | `explainer.py:32` |
| Background samples | Up to 200 random sequences from demo/training data | `explainer.py:35` |
| n_samples | 50 | `explainer.py:78` |
| Target output | Risk score (index=0) | `explainer.py:78` |
| Input | Sequence tensor (1, history_len=4, 25 features) | `explainer.py:76` |

### GradientShap vs SHAP

`GradientShap` (Captum) computes gradient-weighted input perturbation attributions. It is **not** TreeSHAP or KernelSHAP — it is closer to Integrated Gradients with noise injection. For LSTM models this is more appropriate than TreeSHAP (which is for tree models) or KernelSHAP (very slow). The choice is appropriate.

### Sanity Check Results

| Sanity Check | Status | Evidence |
|---|---|---|
| Attributions computed on actual deployed model | ✅ | `AttackExplainer(model=forecaster.model)` — same PyTorch model object | 
| Per-sample (not global average) | ✅ | `explain_window()` called per user interaction |
| Sum of attributions ≠ 0 when attack present | ✅ | `test_explainer` checks `total_shap` is float and not identically zero [RUN] |
| Remove top feature → probability drops | ❌ Not tested | Would require a second forward pass with top feature zeroed |
| Attributions vary across different inputs | ❓ Unverifiable without a running app session | The narrative changes based on `top_driver['feature']`, so likely yes |
| Background is meaningful (not all zeros) | ✅ | Background built from real demo windows `explainer.py:35` |

### Decision Support Review

| Element | Present | Quality |
|---|---|---|
| What is happening | ✅ | MITRE stage name + technique |
| Confidence | ⚠️ | Hard-coded per rule, not probabilistic |
| Windows until compromise | ✅ | K-step timeline chart |
| Which hosts/flows | ⚠️ | Topology tab shows raw flows but doesn't link to risk |
| What to do | ✅ | SOC playbook per stage with 3 steps each |
| Recommended mitigations | ✅ | Network block, isolation, DNS sinkhole, EDR |
| SLA response time | ✅ | P1 < 15 min, P2 < 30 min, etc. |
| MITRE technique IDs | ✅ | T1046, T1110, T1190, T1021, T1071, T1041 |
