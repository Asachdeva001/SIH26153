# SIH26153 — Prediction, ATT&CK Mapping & Explainability Audit (v2)

**Audit Date:** 2026-09-23

## Changelog — Re-audit (frontend/backend split + cloud training)
- **Architecture Shift:** Inference is now served over REST API to a Next.js client.
- **Code Status:** The ML implementation files (`src/world_model.py`, `src/explainer.py`) were deleted. The API endpoints crash on `Depends(get_forecaster)` missing.
- **API Contract Review:** Added analysis of the network payload shapes and latency implications.

---

## 1. Inference Pipeline Walk-Through (Target State)

End-to-end trace from the Next.js UI through the FastAPI backend:

```text
1. UI: User uploads CSV/PCAP -> POST /api/upload
2. FastAPI: upload.py -> TrafficParser.parse_pcap() -> create_time_windows()
3. FastAPI: Returns {windows: [...], raw_packets: [...]} to Next.js
4. UI: Next.js renders Timeline, sends POST /api/forecast with windows
5. FastAPI: forecast.py -> WorldModelForecaster.predict_k_steps(K)
6. FastAPI: Returns {forecast_df: [...], risk_trajectory: [...]}
7. UI: Next.js sends POST /api/mitre with forecast_df[-1]
8. FastAPI: mitre.py -> RuleBasedMITREMapper.map_state_to_stage()
9. UI: Next.js sends POST /api/xai with windows
10. FastAPI: xai.py -> AttackExplainer.explain_window()
```

### Network Payload Skew Analysis
The new API endpoints accept and return raw JSON dictionaries (converted via Pydantic). 

**Issue:** The state vectors passed between Next.js and FastAPI contain 30+ float fields per window. 
- A request to `/api/forecast` with 200 history windows sends ~100KB of JSON.
- A request to `/api/xai` sends another ~100KB of JSON.
While this is acceptable for a local prototype, for a production cloud deployment, this is highly inefficient. The Next.js client should not bounce the entire dataset back and forth; the FastAPI backend should hold the session state in memory (e.g., Redis) and accept a `session_id`.

---

## 2. Output Contract Review (R12, R13, R14)

### R12: Infiltration Probability Time-Series
| Output | Present | Location |
|---|---|---|
| K probability values | ✅ API | `backend/schemas/requests.py:ForecastResponse` |
| Displayed as chart | ✅ UI | `frontend/src/app/components/tabs/ForecastTimeline.tsx` |
| Uncertainty estimate | ❌ | Only point predictions, no confidence interval |

### R13: Predicted ATT&CK Stage
| Output | Present | Location |
|---|---|---|
| Stage name | ✅ API | `MitreResponse` (name, id, technique, confidence) |
| From forecasted state | ✅ UI | Next.js explicitly sends `forecast.forecast_df[length-1]` to the MITRE endpoint. |
| Probabilistic mapping | ❌ | Still relies on hard-coded threshold rules in the deleted `RuleBasedMITREMapper`. |

### R14: Feature Attribution (XAI)
| Output | Present | Location |
|---|---|---|
| Attribution method | ⚠️ API | `backend/routers/xai.py` wires to `AttackExplainer`. |
| Top-10 returned | ✅ API | `XAIAttribution` schema in `requests.py`. |
| Natural language narrative | ✅ API | `narrative: str` in `XAIResponse`. |
| Per-timestep | ✅ API | `per_timestep: List[float]` array passed to UI. |

---

## 3. Explainer Concurrency Bug

In `backend/routers/xai.py`:
```python
@router.post("/xai", response_model=XAIResponse)
def get_xai_attribution(req: XAIRequest, forecaster=Depends(get_forecaster)):
    # ...
    explainer = AttackExplainer(
        model=forecaster.model,
        # ...
        background_df=df_win_sub
    )
    xai_res = explainer.explain_window(...)
```

**Production Flaw:** Captum `GradientShap` computation is extremely CPU-intensive. Because this is executed in a standard `def` endpoint, FastAPI runs it in the default `anyio` threadpool. 
However, PyTorch operations can contend heavily for the GIL and internal C++ threadpools. If 10 users click the XAI tab simultaneously on an AWS ECS container with 2 vCPUs, the server will lock up and fail readiness probes.

**Fix:** XAI must be offloaded to a background task queue (e.g., Celery) or the threadpool size strictly limited via environment variables (`OMP_NUM_THREADS=1`).
