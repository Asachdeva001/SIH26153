# SIH26153 — Evaluation & Benchmarks Audit

**Audit Date:** 2026-09-21

---

## Split Integrity Analysis

| Issue | Status | Evidence | Severity |
|---|---|---|---|
| Random flow-level split | ✅ Not used | `train.py:18-32`: campaign-grouped chronological split | 🟢 |
| Windows overlapping across splits | ✅ Not present | Campaign-level grouping prevents within-campaign overlap | 🟢 |
| Scaler fit on all data | ✅ Correct | `train.py:102-105`: fit only on train split | 🟢 |
| Hyperparameter tuning on test set | ✅ Not done | No grid search | 🟢 |
| Duplicate flows across train/test | ❓ Unverifiable | CIC-IDS-2018 known to have duplicates; not checked | 🟠 |
| Only 1 real campaign (1 CSV file) | 🔴 CRITICAL | With 1 CSV, "campaign-grouped" split collapses to a single train-or-test assignment; temporal split within a day is acceptable but the group-level split produces 0 test campaigns if there is 1 file and it lands in train | 🔴 |

**Observed split behaviour with 1 CSV file [INFER]:**  
`groups = ['02-14-2018.csv']`, `split_idx = int(1 * 0.7) = 0`, so `train_groups = groups[:0] = []`, `test_groups = ['02-14-2018.csv']`. This means the **entire real dataset would be in the test set with nothing in training** — training would fail or produce empty training data. This is a critical bug when using a single CSV file.

---

## Claimed vs. Reproduced Metrics Table

| Metric | Where Claimed | Claimed Value | Reproduced Value | Command/Source | Gap |
|---|---|---|---|---|---|
| World Model F1 | `README.md` / `benchmark_report_synthetic.json` | 0.000 (honest, stored) | Not reproduced on real data | [READ] benchmark_report_synthetic.json:21 | Train-on-synthetic artifact |
| Baseline LR F1 | `benchmark_report_synthetic.json:28` | 0.982 | Not reproduced on real data | [READ] | Train-on-synthetic artifact |
| World Model Lead Time | `README.md:20` "+3.5 windows" | +3.5 | Hard-coded in bar chart (app.py:856) | [READ] app.py:856 | Hard-coded, not computed |
| World Model Precision | `benchmark_report_synthetic.json:22` | 0.000 | — | [READ] | Synthetic |
| World Model Recall | `benchmark_report_synthetic.json:23` | 0.000 | — | [READ] | Synthetic |
| World Model FPR | `benchmark_report_synthetic.json:24` | 0.000 | — | [READ] | Synthetic |
| Baseline Recall | `benchmark_report_synthetic.json:30` | 1.000 | — | [READ] | Synthetic, class-imbalanced |
| Baseline FPR | `benchmark_report_synthetic.json:31` | 0.029 | — | [READ] | Synthetic |
| Gain F1% | `benchmark_report_synthetic.json:34` | -98.2% | — | [READ] | WM loses catastrophically |

**All metrics are from the synthetic training run. No metrics from real CIC-IDS-2018 exist.** The "Claimed, not verified" metrics in the README's performance section are based on the synthetic benchmark.

---

## Root Cause of WM F1 = 0.000

The evaluation pipeline (`train.py:134-149`) computes benchmark as follows:

```python
world_preds = forecaster.predict_k_steps(test_df, K=1)
world_pred_probs = np.array(world_preds['risk_trajectory'])
# world_pred_probs has length 1 (K=1), but len(y_test_gt) could be ~60 windows
if len(world_pred_probs) < len(y_test_gt):
    pad_len = len(y_test_gt) - len(world_pred_probs)
    world_pred_probs = np.concatenate([np.zeros(pad_len), world_pred_probs])
# Result: [0, 0, 0, ..., 0, single_risk_score]
```

This pads the world model predictions with **zeros** to match the test set length, meaning the world model is effectively evaluated as if it predicts zero risk for all but 1 window. At any threshold > 0, almost all predictions are "not attack" → F1 collapses.

**This is not a model quality problem — it is a fundamentally broken evaluation design.** The correct evaluation would be:
1. For each window T in the test set, take the preceding history_len windows
2. Run predict_k_steps(history, K=k) for k=1..K
3. Compare `risk_trajectory[k-1]` against `y_test[T+k]`

---

## Baseline Fairness Review

| Criterion | Status | Evidence |
|---|---|---|
| Same feature columns as WM | ✅ Yes | `BaselineClassifier.feature_cols = FEATURE_COLUMNS` (world_model.py:397) |
| Same train/test split | ✅ Yes | `base.fit(train_df)` in same script | 
| Class weighting | ❌ No | `LogisticRegression(max_iter=1000)` — no `class_weight='balanced'` |
| Scaler applied | ❌ No | `BaselineClassifier.fit()` uses raw `X` (world_model.py:401-403) — not scaled, while WM uses scaled features |
| Sequence-aware fair baseline | ❌ Missing | No lagged-feature LR baseline (e.g., LR on concatenated last 4 windows) |

**Conclusion:** The LR baseline is **slightly handicapped** (no scaling) but this would make it score *lower*, not higher. Given the baseline already scores F1=0.982 on synthetic data (effectively memorising the simple sine-wave-like synthetic patterns), the handicap doesn't change the verdict. For real data, a fair baseline needs proper class weighting and feature scaling.

---

## Forecasting-Specific Metrics Assessment

| Metric | Present | Notes |
|---|---|---|
| Next-state prediction error (MSE vs persistence baseline) | ❌ Missing | No comparison of `state_decoder` output vs "S_t+1 = S_t" baseline |
| Infiltration-prediction metrics per horizon (t+1 … t+K) | ❌ Missing | Current evaluation only uses K=1, padded with zeros |
| Early-warning lead time (windows before GT compromise) | ❌ Missing properly | The +3.5 value in README is hard-coded in app.py:856, not computed |
| False alarms per hour/day on benign-only traffic | ❌ Missing | No operational FPR measurement |
| Stage-classification accuracy / confusion matrix | ❌ Missing | MITRE stage prediction never evaluated quantitatively |
| PR-AUC | ❌ Missing | Only F1/precision/recall/FPR at fixed thresholds |
| ROC-AUC | ❌ Missing | |
| Calibration (Brier score / ECE) | ❌ Missing | |
| Rollout error accumulation curve | ❌ Missing | |

---

## Recommended Evaluation Protocol

The following is the evaluation protocol the team should adopt before submission:

### Step 1: Fix Label Engineering
```python
# In train.py, after parse_csv(), map the Label column:
label_map = {
    'BENIGN': 0.05,
    'Bot': 0.85,          # C2
    'DoS attacks-GoldenEye': 0.50,  # Initial Access / DoS
    'DoS attacks-Slowloris': 0.50,
    'DoS attacks-SlowHTTPTest': 0.50,
    'DoS attacks-Hulk': 0.50,
    'FTP-BruteForce': 0.45,  # Initial Access
    'SSH-Bruteforce': 0.45,
    'Infilteration': 0.90,  # Lateral Movement / Exfiltration
    'DDOS attack-HOIC': 0.70,
    'DDOS attack-LOIC-UDP': 0.70,
}
df['target_risk_score'] = df['label'].map(label_map).fillna(0.05)
```

### Step 2: Correct Evaluation Methodology
```python
def evaluate_k_step_forecast(forecaster, test_df, K=5, threshold=0.5):
    results = {k: [] for k in range(1, K+1)}
    for t in range(len(test_df) - K):
        history = test_df.iloc[max(0, t-4):t+1]
        pred = forecaster.predict_k_steps(history, K=K)
        for k in range(1, K+1):
            future_gt = test_df.iloc[t+k]['target_risk_score'] > 0.30
            predicted_risk = pred['risk_trajectory'][k-1]
            results[k].append((predicted_risk, int(future_gt)))
    # Compute F1, precision, recall, AUC per k
```

### Step 3: Metrics to Report

| Metric | Description |
|---|---|
| F1@k (k=1..5) | F1 score for each forecast horizon |
| AUC-ROC | Overall discrimination |
| PR-AUC | Precision-recall under imbalance |
| Lead time (windows) | Median windows before GT compromise at which WM first exceeds threshold |
| FP rate (per hour) | False positives on benign-only traffic segments |
| Persistence baseline MSE | `||S_t+1_hat - S_t||_2` vs `||S_t+1_actual - S_t||_2` |
| Stage accuracy | Accuracy of MITRE stage prediction on labeled test windows |
| LR baseline F1 (same split) | Fair comparison |

### Step 4: Cross-Dataset Test
Download at least one CTU-13 scenario CSV. Train on CIC-IDS-2018, test on CTU-13. Report generalisation gap.
