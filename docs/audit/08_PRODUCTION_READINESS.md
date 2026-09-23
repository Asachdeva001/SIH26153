# SIH26153 — Production Readiness Audit

**Audit Date:** 2026-09-21

---

## Architecture & Code Quality

| Area | Rating | Findings |
|---|---|---|
| **Separation of concerns** | 🟠 | `app.py` (929 lines) is a "god-file": contains all UI logic, model loading, inference, evaluation display. No clean service layer. |
| **Circular imports** | ✅ | No circular imports found |
| **God-files** | 🟠 | `world_model.py` (454 lines) contains 5 unrelated classes: `PyTorchTransitionLSTM`, `WorldModelForecaster`, `RuleBasedMITREMapper`, `AssetCriticalityManager`, `SOCRiskPrioritizer`, `BaselineClassifier`, `BenchmarkEvaluator` — these should be split into separate modules |
| **Notebook code** | ✅ | No notebooks present |
| **Interface between layers** | 🟠 | `FEATURE_COLUMNS` constant shared via import (good), but no typed data contracts (Pydantic/TypedDict) between layers |
| **Pattern consistency** | 🟡 | Mix of class methods, instance methods, and static methods without clear rationale |

### Top Complexity Hotspots

| File | Lines | Issue |
|---|---|---|
| `app.py` | 929 | Entire dashboard in one file; should be split into `ui/tabs/*.py` |
| `world_model.py` | 454 | 7 different classes, none related by inheritance |
| `src/parser.py` | 375 | `create_time_windows()` (lines 195-332) is 137 lines — extract to separate function |
| `src/synthetic_generator.py` | 324 | `_generate_apt_multistage()` is 190 lines — extract per-phase packet generator |

---

## Configuration

| Issue | Status | Location |
|---|---|---|
| Config-driven training | ✅ | `configs/default.yaml` loaded by `train.py:35-44` |
| Hard-coded magic numbers | ⚠️ | `app.py:856` hard-codes `3.5`; `app.py:491` hard-codes `0.15`; `parser.py:183` hard-codes `0.05` for PCAP flow_duration; `world_model.py:96` hard-codes batch_size=1024 |
| Env var handling | ❌ | Only `KAGGLE_USERNAME`/`KAGGLE_KEY` referenced, via `load_dotenv()` in `download_dataset.py` — but `dotenv` not in `requirements.txt` |
| `.env.example` | ❌ | No `.env.example` file. Real credentials in `.env`. |

---

## Testing

| Area | Status | Evidence |
|---|---|---|
| Tests run | ✅ | `python -m pytest tests/test_pipeline.py -v` → **9 passed, 1 warning in 16.48s** [RUN] |
| Feature extractor tests | ✅ | `test_traffic_parser_correctness`: checks `total_bytes=1000` and `syn_flag_ratio=1.0` |
| Windowing tests | ✅ | Implicit in parser test |
| Label derivation | ⚠️ | No test for real CIC-IDS label parsing |
| Rollout tests | ✅ | `test_world_model_forecast`: verifies K=5 trajectory length |
| ATT&CK mapping | ✅ | `test_mitre_mapper`: checks Exfiltration classification |
| Leakage prevention | ✅ | `test_no_leakage_chronological_split`: asserts disjoint campaign sets |
| Explainer | ✅ | `test_explainer`: checks attribution count and narrative presence |
| CI pipeline | ❌ | No `.github/workflows/` |
| Coverage reporting | ❌ | No `pytest --cov` configured |

---

## Error Handling & Robustness

| Scenario | Handled? | Evidence | Fix |
|---|---|---|---|
| Malformed CSV | ❌ | No try/except in `parse_csv()` | Wrap in try/except, return `st.error()` |
| Empty PCAP | ❌ | `packets_data = []` → `pd.DataFrame([])` → downstream IndexError | Check `len(packets_data) == 0` |
| Missing columns in CSV | ✅ | `_ensure_column()` fills defaults silently | |
| NaN propagation | ⚠️ | `ttl_std` guards for NaN (parser.py:288) but `flow_iat_std**2` can NaN | Add `np.nan_to_num()` on IAT features |
| Empty window sequence | ✅ | `world_model.py:84-86`: returns early if no sequences | |
| Zero-division | ✅ | `max(1, ...)` guards throughout | |
| Timeouts | ❌ | No timeout on model inference or parse | |
| Huge inputs (1 GB PCAP) | ❌ | Full RAM load; no chunked parsing | |
| Corrupt model weights | ❌ | No validation of loaded weights | |
| `df_win` empty after parse | ❌ | `app.py:472`: `iloc[-1]` crashes on empty DF | |

---

## Performance

| Measurement | Estimate | Method | Notes |
|---|---|---|---|
| Window aggregation speed | ~500 windows/sec | [INFER] based on tqdm-reported batch size | 10,000 windows ≈ 20 sec |
| LSTM inference (K=5) | <0.1 sec | [INFER] 64-unit, 25-feature LSTM | Negligible for interactive use |
| GradientShap attribution | 2–5 sec | [INFER] n_samples=50 on history_len=4 | Can block UI; add spinner |
| CSV parse (358 MB) | ~30–60 sec | [INFER] pandas read_csv on Windows | Memory: ~1.5 GB peak |
| PCAP parse throughput | Scapy: ~5,000 pkts/sec | [INFER] known Scapy performance | 100k packet PCAP ≈ 20 sec |

---

## Security Checklist

| Item | Status | Evidence | Fix |
|---|---|---|---|
| Kaggle API key in .env (tracked in git) | ❌ CRITICAL | `.env:1-2` [READ]: real credentials | Rotate key immediately; add `.env` to `.gitignore` (already there but file is tracked — run `git rm --cached .env`) |
| `torch.load(weights_only=False)` on user-uploaded path | ❌ HIGH | `world_model.py:148` [READ] | Change to `weights_only=True` or validate file before loading; only load from `models/` |
| File path traversal via upload filename | ⚠️ | `app.py:396`: `os.path.join("scratch", uploaded_file.name)` | Sanitise filename with `os.path.basename()` |
| Flask debug mode | N/A | Streamlit app, no Flask | |
| CORS | ⚠️ | `render.yaml`/`Procfile` disables CORS protection (`--server.enableCORS false`) | Acceptable for demo; not for production |
| File type validation | ⚠️ | Streamlit `type=['pcap','pcapng','csv']` — client-side check only | Add server-side MIME type check |
| Pickle unsafe deserialization | ⚠️ | `joblib.load('models/baseline_lr_v1.pkl')` — if user supplied, dangerous; but file path is hardcoded to `models/`, not user-supplied | Acceptable; document |
| Secrets in code | ✅ | No API keys hardcoded in Python files | |
| SQL injection | N/A | No database | |
| Logging of sensitive data | ✅ | No IP/payload logging found | |
| Docker running as root | ⚠️ | `Dockerfile` has no `USER` directive → runs as root | Add `RUN useradd -r appuser && USER appuser` |

---

## MLOps

| Aspect | Status |
|---|---|
| Model versioning | ❌ — single `world_model_v1.pth`, no version metadata in filename |
| Dataset versioning (DVC) | ❌ — no DVC, no dataset hash |
| Experiment tracking | ❌ — no MLflow/W&B/TensorBoard |
| Model card | ❌ — no model card |
| Reproducible environment | ⚠️ — unpinned `>=` versions; no lockfile |
| CI that lints + tests | ❌ — no `.github/workflows/` |

---

## Technical Debt Register

| Item | File | Line(s) | Severity | Effort | Notes |
|---|---|---|---|---|---|
| Hard-coded benchmark lead-time in chart | `app.py` | 856 | 🔴 | S | Replace `3.5` with computed value |
| Risk target all-zeros for real data | `world_model.py` | 66-69 | 🔴 | M | Implement CIC-IDS label→risk_score mapping |
| `torch.load(weights_only=False)` | `world_model.py` | 148 | 🔴 | S | Use `weights_only=True` or validate input |
| Kaggle credentials committed | `.env` | 1-2 | 🔴 | S | Rotate, remove from tracked files |
| CDN Google Fonts call | `app.py` | 26 | 🔴 | S | Bundle fonts locally |
| No error handling on file upload | `app.py` | 393-414 | 🔴 | S | Add try/except |
| `iloc[-1]` crash on empty DF | `app.py` | 472 | 🔴 | S | Guard with empty check |
| `python-dotenv` missing from requirements | `requirements.txt` | — | 🟠 | S | Add `python-dotenv>=1.0.0` |
| No pinned dependency versions | `requirements.txt` | all | 🟠 | S | Run `pip freeze > requirements.lock` |
| `world_model.py` god-class | `world_model.py` | all | 🟠 | M | Split into `model.py`, `mapper.py`, `evaluator.py`, `soc.py` |
| `app.py` god-file | `app.py` | all | 🟠 | L | Split into `ui/` submodule with one file per tab |
| No retransmission detection in PCAP | `parser.py` | 183 | 🟠 | M | Implement TCP SYN+SYN-ACK state machine |
| flow_duration hardcoded=0.05 in PCAP | `parser.py` | 173 | 🟠 | M | Implement per-flow TCP session tracking |
| `fillna(method='ffill')` deprecated | `parser.py` | 73 | 🟡 | S | Use `ffill()` method call |
| No type hints on most functions | all | — | 🟡 | M | Add type annotations |
| No CI pipeline | — | — | 🟡 | S | Add `.github/workflows/test.yml` |
| No Docker `USER` directive | `Dockerfile` | all | 🟡 | S | Add non-root user |
| Scaler double-applied (pth + pkl) | `app.py` | 314-316 | 🟡 | S | Remove redundant scaler override after model load |
| `shap>=0.44.0` in requirements but never imported | `requirements.txt` | 9 | 🟢 | S | Remove or actually use it |
| CUDA determinism not set | `train.py` | — | 🟢 | S | Add `torch.backends.cudnn.deterministic = True` |

---

## Dependency & Licence Audit

| Package | Version Req | Licence | Notes |
|---|---|---|---|
| torch | ≥2.0.0 | BSD-3-Clause | ✅ |
| scikit-learn | ≥1.4.0 | BSD-3-Clause | ✅ |
| pandas | ≥2.0.0 | BSD-3-Clause | ✅ |
| numpy | ≥1.24.0 | BSD-3-Clause | ✅ |
| scipy | ≥1.10.0 | BSD-3-Clause | ✅ |
| streamlit | ≥1.30.0 | Apache-2.0 | ✅ |
| plotly | ≥5.18.0 | MIT | ✅ |
| scapy | ≥2.5.0 | GPL-2.0 | ⚠️ GPL — acceptable for source distribution, note in README |
| captum | ≥0.7.0 | BSD-3-Clause | ✅ |
| shap | ≥0.44.0 | MIT | ✅ Listed but unused |
| pyyaml | ≥6.0.0 | MIT | ✅ |
| joblib | ≥1.3.0 | BSD-3-Clause | ✅ |
| pytest | ≥7.4.0 | MIT | ✅ |
| kaggle | ≥1.6.0 | Apache-2.0 | ✅ |
| tqdm | ≥4.65.0 | MIT | ✅ |
| python-dotenv | Not listed | BSD-3-Clause | ❌ Missing from requirements.txt |

---

## Environment Variable Reference

| Variable | Required | Used In | Purpose | Example |
|---|---|---|---|---|
| `KAGGLE_USERNAME` | ✅ (for dataset download) | `scripts/download_dataset.py` | Kaggle API authentication | `karrtikgupta` |
| `KAGGLE_KEY` | ✅ (for dataset download) | `scripts/download_dataset.py` | Kaggle API key | `KGAT_...` (**EXPOSED IN .env — ROTATE IMMEDIATELY**) |
| `PORT` | ❌ (optional, Render only) | `Dockerfile`, `Procfile` | Port binding for Render.com | `8501` |
