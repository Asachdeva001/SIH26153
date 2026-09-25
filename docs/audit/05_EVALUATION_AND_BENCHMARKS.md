# SIH26153 — Evaluation & Benchmarks Audit (v2)

**Audit Date:** 2026-09-23

## Changelog — Re-audit (frontend/backend split + cloud training)
- **Code Status:** The ML evaluator logic was located inside the deleted `src/world_model.py`. 
- **API integration:** The new endpoint `backend/routers/benchmark.py` serves the benchmark data but relies on the flawed evaluation methodology from the previous iteration.
- **Cloud Note:** Proper benchmark evaluation across the full 10-day dataset will require the cloud compute environment defined in `13_CLOUD_TRAINING_AND_DEPLOYMENT.md`.

---

## 1. The F1=0.000 Negative Result

In the previous audit, it was discovered that the saved artifact (`models/benchmark_report_synthetic.json` — now deleted from git but the logic remains the same) showed **World Model F1 = 0.000** and Baseline F1 = 0.982. 

The World Model was being beaten by a simple Logistic Regression baseline by 98 percentage points.

### Root Cause (Still present in API)
The evaluation methodology is fundamentally broken. Look at the new API implementation:

```python
# backend/routers/benchmark.py
wm_preds = np.array(req.risk_trajectory)
# Baseline predictions for the same future window (static)
base_preds = baseline.predict_proba(df_win)[-req.K:]
gt_binary = (wm_preds > 0.40).astype(int) # <--- FATAL FLAW
```

1. **`gt_binary` is derived from the model's own predictions!** `gt_binary = (wm_preds > 0.40).astype(int)`. This means there is no actual ground truth being evaluated. The model's predictions are being compared against themselves.
2. In the older training script, the World Model was asked to predict $K$ steps ahead, but it was evaluated against the $t=0$ current ground truth labels. Since the risk of an attack *changes* over $K$ steps, comparing a future prediction to a present label guarantees a score of 0.

---

## 2. Fabricated Lead-Time Advantage

The UI requires a metric showing the temporal advantage (lead time) of the World Model over the baseline.

**Previous UI:** Hardcoded to `3.5` windows.
**New UI (`frontend/src/app/components/tabs/Benchmark.tsx`):**
```tsx
const leadTimeAdv = benchmarkData.lead_time_advantage || 0;
// Renders the leadTimeAdv value directly
```

The new UI correctly reads from the API response instead of hardcoding the value in the frontend. However, because the backend evaluation logic is broken (comparing the model against itself), any lead time returned by `BenchmarkEvaluator` will be meaningless once the code is restored.

---

## 3. Recommended Evaluation Protocol (Cloud Training)

To produce honest metrics for the SIH evaluators, the team must implement a proper K-horizon evaluation loop during the cloud training phase. 

This should be executed on an AWS/GCP instance over a held-out test set from the CIC-IDS-2018 dataset.

```python
# PROPOSED CLOUD EVALUATION LOGIC
def evaluate_k_horizons(model, test_df, max_k=5):
    results = {}
    for k in range(1, max_k + 1):
        y_true = []
        y_pred = []
        
        # Iterate over test set, predicting exactly k steps ahead
        for t in range(history_len, len(test_df) - k):
            history = test_df.iloc[t-history_len : t]
            true_label = test_df.iloc[t+k]['target_risk_score']
            
            # Autoregress K times
            pred = model.predict_k_steps(history, K=k)
            pred_k_risk = pred['risk_trajectory'][-1]
            
            y_true.append(true_label > 0.5)
            y_pred.append(pred_k_risk > 0.5)
            
        results[f'F1@{k}'] = f1_score(y_true, y_pred)
    return results
```

This matrix of metrics ($F1@1, F1@2 ... F1@K$) should be saved as `benchmark_report.json` and served directly by the API.
