# SIH 26153 — `src/` Reconstruction Spec

**Use this only if `Task 0.1, Step A` (git restore) genuinely finds nothing.** This spec reconstructs the deleted ML core module-by-module from two sources that survived the deletion:

1. **The call sites** — `backend/routers/*.py`, `backend/schemas/requests.py`, `backend/models/loader.py` still import and call these modules with specific function names, arguments, and expected return shapes.
2. **The audit reports' documented findings** — written *before* the deletion (or reconstructed from the committed artifacts that did survive, like `frontend/src/lib/types.ts`), which recorded the exact feature list, model architecture, loss function, and known bugs of the original implementation.

Treat every item below tagged **[CONTRACT]** as non-negotiable (the API/frontend will break otherwise) and every item tagged **[REBUILD]** as "recreate the logic to match this documented behavior, using clean code — do not reintroduce the bugs noted."

---

## 0. Before you start: reconcile every call site

For each router in `backend/routers/`, list every function/class it imports from `src.*` and the exact signature it calls (positional/keyword args, return type expected by the corresponding Pydantic response model in `backend/schemas/requests.py`). Build this table first — it is your real spec, more authoritative than anything below if the two ever disagree.

```
Router file | Imports from src.* | Called as | Expected return (per schema)
```

---

## 1. `src/parser.py` — `TrafficParser`

**[CONTRACT]** Called from `backend/routers/upload.py` as roughly:
```python
parser = TrafficParser()
df_parsed = parser.parse_csv(path)        # CSV path
# and/or
raw_packets, df_parsed = parser.parse_pcap(path)   # PCAP path
windows = parser.create_time_windows(df_parsed)    # windowing
```
Confirm exact method names/args against the actual router code — the above is the documented shape from `06`'s inference pipeline walkthrough; adjust to match what `upload.py` literally calls.

**[REBUILD] Feature set — 25 features total** (per `03`), split flow-level and packet-level:

### Flow-level (always computable from CSV or PCAP):
| Feature | Notes |
|---|---|
| `flow_count` | flows per window |
| `total_packets` | |
| `total_bytes` | |
| `syn_ratio`, `ack_ratio`, `fin_ratio`, `rst_ratio`, `psh_ratio`, `urg_ratio` | TCP flag bitmask ratios |
| `iat_mean`, `iat_variance` | inter-arrival time stats — **known bug in the old PCAP parser: it treated every packet as a new flow, corrupting IAT.** Group packets into flows correctly by 5-tuple (src IP, dst IP, src port, dst port, protocol) before computing IAT — do not repeat this bug. |
| port-scan score | heuristic on unique-destination-port count / sequential vs randomised port access pattern |
| `unique_src_ips`, `unique_dst_ips` | |

### Packet-level (only truly available from real PCAP; CSV must not silently fake these — see §1a):
| Feature | Notes |
|---|---|
| `ttl_mean`, `ttl_std` | from IP header TTL, per session |
| `tcp_window_mean` | TCP window size |
| `ip_frag_ratio` | IP fragmentation flag ratio |
| `retrans_ratio` | retransmission count/ratio — **previously hardcoded to 0 in both paths; per Agent Task 2.3 (P2-3 in the old plan) implement real detection via TCP sequence/ack number analysis in the PCAP path.** |

**[REBUILD — honesty fix, not just restoration] §1a — CSV packet-level feature handling:**
The old `_ensure_column` function silently filled missing packet-level columns with constants (`ttl_mean=64`, `tcp_window_mean=64240`, `ip_frag_ratio=0.0`, `retrans_ratio=0.0`) when parsing a CSV that doesn't actually contain them (per `03`). **Do not silently reintroduce this as unlabeled fake data.** Instead:
- Add an explicit boolean/metadata flag on the parsed output (e.g., `packet_level_features_available: bool`) that the API surfaces to the frontend, so the UI can honestly disclose "packet-level features are estimated defaults for CSV input" instead of presenting fabricated numbers as real.
- Still fill the columns with the same sensible constants (the model needs a fixed-width feature vector), but the constant-fill must be **visible and documented**, not silent.

**[CONTRACT]** `create_time_windows()` — must produce a structured feature vector per time window (per `04`'s documented model input shape: `1 x 4 x 25`, i.e., a history of 4 windows × 25 features). Confirm the exact history length and feature count against `src/world_model.py`'s expected input shape (§2 below) and the frontend's window-rendering code (`frontend/src/app/components/tabs/ForecastTimeline.tsx` and `lib/types.ts`) rather than assuming 4/25 are still correct — those may have changed; treat the numbers here as a strong prior, not gospel.

---

## 2. `src/world_model.py` — `PyTorchTransitionLSTM`, `WorldModelForecaster`, `AssetCriticalityManager`

**[REBUILD] Architecture (documented in `04`):**

```
Input window T, shape (batch=1, seq_len=4, features=25)
  -> 2-layer LSTM, hidden_size=64
  -> hidden state feeds two heads:
       - State Decoder: Linear(64 -> 25)   -> predicted next-state vector S_{t+1}
       - Risk Head: Linear(64 -> 16) -> Linear(16 -> 1) -> Sigmoid -> risk probability
  -> Predicted next state S_{t+1} is fed back into the input (autoregressive) for K steps
```
- **Parameter count:** ~64,000 — this is a small model; a single T4/L4 GPU (or even CPU) trains it fast. Don't over-build this.
- **[REBUILD] Loss function:**
  `L = MSE(Ŝ_{t+1}, S_{t+1}) + 2.0 × BCE(R̂_{t+1}, R_{t+1})`
  i.e., dual-head loss — next-state regression (MSE) plus risk classification (BCE), risk term weighted 2×. Keep this weighting as a starting point but treat it as a tunable hyperparameter, not a fixed constant, and log whatever value is actually used in the final training config for reproducibility (R10).
- **[CONTRACT]** `WorldModelForecaster.predict_k_steps(df_window, K)` — must return a **true autoregressive rollout**: each step's predicted state feeds into the next step's input, not K independent forward passes and not the same prediction repeated K times (per the original audit's "genuine world model" verdict criteria — this is the difference between a real world model and a classifier wearing a world-model costume, so get it right). Return shape should match what `backend/routers/forecast.py`'s `ForecastResponse` schema expects — check `backend/schemas/requests.py` for the exact field names (`forecast_df`, `risk_trajectory`, etc., per `04`/`06`).
- **[REBUILD]** `AssetCriticalityManager` — referenced by `backend/routers/soc.py` (per `09`); reconstruct its interface from that router's call site. If the exact original logic can't be inferred, implement a reasonable version (e.g., tiering assets/hosts by a configurable criticality score used to prioritize SOC playbook recommendations) and flag it in the verification log as "functionally equivalent reconstruction, not verified against original logic" — this is an acceptable gap to disclose rather than silently invent with false confidence.

---

## 3. `src/synthetic_generator.py` — `SyntheticAttackGenerator`

**[REBUILD]** Used previously to produce the only training data the model ever saw (per `04`'s "Training Status (Synthetic Only)" finding). Reconstruct a generator that produces plausible benign vs. attack-pattern time-series feature windows for the same 25-feature schema as §1/§2, useful now specifically as a **fast sanity-check dataset** (per Agent Task 2.1's "quick sanity pass on synthetic data first") — not as the final training data. Keep it simple: this doesn't need to be sophisticated, it needs to exercise the training loop correctly and quickly.

---

## 4. `src/mitre_mapper.py` — `RuleBasedMITREMapper`

**[CONTRACT]** Called from `backend/routers/mitre.py` as `map_state_to_stage(...)`, returning stage `name`, `id`, `technique`, `confidence` (per `06`'s output contract table for R13).

**[REBUILD]** Map predicted future states (from `WorldModelForecaster.predict_k_steps`) to the five required MITRE ATT&CK stages: Reconnaissance, Initial Access, Lateral Movement, Command & Control, Exfiltration. Build this as a documented, defensible rule table (e.g., dominant feature signatures per stage: high port-scan score + low bytes → Reconnaissance; high SYN ratio + single dst → Initial Access attempt; etc.) with **real MITRE technique IDs** attached (e.g., T1595 Active Scanning, T1110 Brute Force, T1071 Application Layer Protocol, T1041 Exfiltration Over C2 Channel) — do not invent technique IDs, look them up. **This mapping needs human domain-expert review before the demo — see `HUMAN_TASKS.md` item S5. Do not treat your reconstructed version as final without that review.**

---

## 5. `src/explainer.py` — `AttackExplainer`

**[CONTRACT]** Called from `backend/routers/xai.py`:
```python
explainer = AttackExplainer(model=forecaster.model, background_df=df_win_sub, ...)
xai_res = explainer.explain_window(...)
```
Returns attributions matching `XAIResponse` schema — per `06`: top-10 feature attributions, a natural-language narrative string, and a per-timestep attribution array.

**[REBUILD]** Use Captum (already a declared dependency per `02`'s tech stack table — `Captum GradientShap`) against the reconstructed `PyTorchTransitionLSTM`. Implement:
- `GradientShap` (or `IntegratedGradients` as a fallback if GradientShap proves unstable on the small LSTM) computing per-feature attribution for a given prediction.
- A simple template-based narrative generator that turns the top attributed features into a human-readable sentence (e.g., "Elevated SYN ratio and low IAT variance are driving this window's risk score").
- **Sanity check requirement (from the original audit's explainability criteria):** after building this, verify attributions are not static/global — run it on two different windows and confirm the top features differ when the input differs.

---

## 6. `src/evaluator.py` — K-horizon evaluation (new module; the original had this logic inline and buggy)

**[REBUILD — this one must be built correctly from scratch, not just restored/guessed]** Per `05`'s root-cause finding, the original evaluation compared the model's predictions to a "ground truth" derived from the model's own output (`gt_binary = (wm_preds > 0.40).astype(int)`), which is meaningless. Do not reconstruct that logic even though it's "documented" — it's documented as a **bug**, not a spec to follow. Build the corrected version instead:

```python
def evaluate_k_horizons(model, test_df, max_k=5, history_len=4):
    """
    For each horizon k in 1..max_k, walk the test set, predict k steps
    ahead from real history, and compare against the REAL future label
    at t+k (not the model's own current-step output).
    """
    results = {}
    for k in range(1, max_k + 1):
        y_true, y_pred = [], []
        for t in range(history_len, len(test_df) - k):
            history = test_df.iloc[t - history_len : t]
            true_label = test_df.iloc[t + k]['target_risk_score']
            pred = model.predict_k_steps(history, K=k)
            pred_k_risk = pred['risk_trajectory'][-1]
            y_true.append(true_label > 0.5)
            y_pred.append(pred_k_risk > 0.5)
        results[f'F1@{k}'] = f1_score(y_true, y_pred)
        results[f'precision@{k}'] = precision_score(y_true, y_pred)
        results[f'recall@{k}'] = recall_score(y_true, y_pred)
        results[f'fpr@{k}'] = false_positive_rate(y_true, y_pred)  # implement or import
    return results
```
This is the same function sketched in the audit's `05` report — build it as the primary/only evaluation path, wired into `backend/routers/benchmark.py`.

Also implement a fair **logistic-regression baseline** trained on the exact same feature set and split (per `05`'s fairness requirement) for comparison — do not let the baseline see extra features or a friendlier split than the world model gets.

---

## 7. Cross-check against the frontend before declaring done

Once all modules above exist and the backend boots, do a **field-by-field diff** between:
- `backend/schemas/requests.py` (Pydantic response models)
- `frontend/src/lib/types.ts` (hand-written TypeScript interfaces, per `06`/`08`'s drift-risk warning)

Any mismatch here means either the reconstruction guessed a field name wrong, or the frontend types were already stale before the deletion — fix whichever is wrong, and note in the verification log which one it was.

---

## 8. What "done" looks like for this spec

- All six modules exist, import cleanly, and match every call site in `backend/routers/`.
- The model is **untrained** at this point — that's expected and correct; Phase 2 trains it.
- The evaluator is the corrected version, not the buggy original.
- The CSV packet-level feature faking is now disclosed via a flag, not silent.
- The MITRE mapping and label-severity mapping are flagged for human review (`HUMAN_TASKS.md` S4/S5) before being treated as final.
- Every reconstructed function/class has at least one Phase 3 unit test (Task 3.4) proving it does what its call site expects.
