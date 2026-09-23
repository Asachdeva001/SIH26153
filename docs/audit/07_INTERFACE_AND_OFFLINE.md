# SIH26153 — Interface & Offline Audit

**Audit Date:** 2026-09-21

---

## Interface Identification

The interface is a **Streamlit web application** (`app.py`, 929 lines) with:
- 8 tabs: Forecast Timeline, MITRE ATT&CK Tracker, XAI Feature Attribution, K-Step Simulator, SOC Response, Model Benchmarking, Network Topology, Audit Report
- A sidebar with: data source selector, asset IP picker, K-step slider, window slider, alert threshold slider, SOC-tunable MITRE rules expander
- Dark "cyber command" theme with Orbitron/JetBrains Mono fonts

---

## File/Format Support Matrix

| Format | Accepted? | Code Location | Works? | Notes |
|---|---|---|---|---|
| `.csv` | ✅ Yes | `app.py:393,401` | ✅ Yes | `parse_csv()` with column mapping |
| `.pcap` | ✅ Yes | `app.py:393,403` | ✅ Yes (if Scapy installed) | `parse_pcap()` with Scapy fallback |
| `.pcapng` | ✅ Yes | `app.py:393` | ✅ Yes (if Scapy installed) | Same as pcap |
| Wrong format | ❌ Not handled | — | ❌ Crash | Streamlit blocks other extensions at upload, but wrong content (e.g., CSV named as pcap) will crash `parse_pcap()` |
| Empty file | ❌ Not handled | — | ❌ Crash | `create_time_windows()` returns empty DF then `iloc[-1]` crashes at `app.py:472` |
| Very large file (>100 MB) | ❌ Not handled | — | ⚠️ Slow/OOM | `parse_csv()` does `pd.read_csv()` on entire file; 358 MB CSV loads into RAM |
| File size limit | ❌ None set | — | — | Streamlit default is 200 MB; no project-level limit |

---

## Fake-Demo Detector Results

| Red Flag | Found? | Location | Severity |
|---|---|---|---|
| Hard-coded/demo-only data path | ✅ FOUND (synthetic) | `app.py:300-304`: `session_state` initialised with synthetic APT scenario on every fresh start | 🟠 Intentional but should be disclosed |
| Results don't change with input | Partial | Risk trajectory DOES change with different uploaded inputs; MITRE stage DOES change. BUT benchmark bar chart has hard-coded 3.5 | 🔴 |
| Hard-coded values in chart | ✅ FOUND | `app.py:856`: `y=[...3.5]` — the Lead Time bar is always 3.5 regardless of actual lead time | 🔴 |
| Pre-baked images | ❌ Not found | — | 🟢 |
| Random-generated charts | ❌ Not found | — | 🟢 |
| Buttons that do nothing | ⚠️ Partial | SOC action buttons (`Isolate Host`, `Subnet Micro-Segment`, `Acknowledge Analyst`) only set a status string — no real network action (acceptable for demo, but must be disclosed) | 🟡 |
| Canned output | ❌ Not found | Model is loaded and called; outputs are genuine model outputs | 🟢 |
| Sample data returned regardless of input | ❌ Not found | If upload fails, old session_state.df_win is used (implicit fallback) | 🟡 |

---

## Offline Audit Table

| Location | Network Call / Asset | Type | Blocks R17? | Fix |
|---|---|---|---|---|
| `app.py:26` | `@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600...')` | CSS Google Fonts CDN | 🔴 **YES** — browser loads this on every page render | Bundle fonts locally: download `.woff2` files, embed as base64 in CSS, or use `st.markdown` with local paths |
| `scripts/download_dataset.py:4,17` | `KaggleApi().authenticate()` + `api.dataset_download_file()` | Kaggle API (runtime) | 🟠 Required only at setup, not at inference runtime | Document as setup-only step; ship pre-downloaded dataset or provide offline setup instructions |
| `render.yaml` | Render.com hosting | Deployment config | 🟡 Cloud hosting reference but not a runtime dependency | Note that local/Docker deployment satisfies offline requirement |
| Plotly charts | Plotly JS served by Streamlit | Bundled with Streamlit | ✅ No — Streamlit bundles Plotly | 🟢 |
| Streamlit telemetry | `streamlit.io` usage stats | Optional telemetry | ⚠️ Enabled by default | Add `.streamlit/config.toml` with `[browser] gatherUsageStats = false` |

**Verdict on R17:** The app has **one hard runtime internet dependency** (Google Fonts CDN at line 26 of app.py). In a strict air-gapped environment, this would cause CSS import errors or slow loading. All model inference, data processing, and computation are fully local. Removing the CDN call is a 15-minute fix.

---

## UI/UX Issues Table

| Problem | File | Line | Impact | Suggested Fix |
|---|---|---|---|---|
| No error handling for empty file upload | `app.py` | 392-414 | 🔴 H — app crashes with `iloc[-1]` on empty DF | Wrap upload parsing in try/except; show `st.error("File appears to be empty or unparseable.")` |
| No error handling for malformed CSV | `app.py` | 401-402 | 🔴 H — exception propagates to Streamlit | Try/except around `parse_csv()` |
| Hard-coded benchmark bar value | `app.py` | 856 | 🔴 H — misleads judges about lead time | Compute dynamically from `bench_res['world_model']['lead_time_windows']` |
| `target_risk_score` assumed in session data for observed risk | `app.py` | 491 | 🟠 M — if column absent, `get()` returns 0.15 (magic number default) | Compute from model output instead |
| Observed Risk card reads from `target_risk_score` not from model | `app.py` | 491 | 🟠 M — shows ground-truth label as "observed risk" (cheating at inference time) | Use `model.predict_k_steps(current_single_window, K=1)` for current risk |
| No loading spinner during XAI computation | `app.py` | 654-665 | 🟡 M — GradientShap takes 2-5 seconds; UI freezes | Add `st.spinner("Computing feature attributions...")` |
| No progress feedback for large file parsing | `app.py` | 395-414 | 🟡 M — 358 MB CSV takes >30 seconds; no feedback | Add progress bar or `st.info()` message |
| `st.sidebar.number_input` called without `key` parameter (SOC tunable rules) | `app.py` | 441-452 | 🟡 M — Streamlit may produce duplicate widget warnings | Add unique `key=` to each |
| Font fallback ugly without Google Fonts | `app.py` | 26-295 | 🟠 M — Orbitron not installed on most systems; fallback is sans-serif | Bundle fonts locally |
| Topology tab shows only first 50 rows | `app.py` | 879 | 🟢 L — `df_raw_sub = df_raw.head(50)` is arbitrary | Add pagination or filter |

---

## Quick Wins (< 1 hour)

1. **Remove Google Fonts CDN call** → embed Orbitron/JetBrains Mono as base64 in CSS or use system-installed fallbacks. (~15 min)
2. **Fix hard-coded 3.5 bar chart** → replace `y=[...,3.5...]` with computed `bench_res['world_model']['lead_time_windows']`. (~10 min)
3. **Add try/except around file upload** → wrap parse_csv/parse_pcap in try/except with `st.error()`. (~20 min)
4. **Add `.streamlit/config.toml`** to disable telemetry. (~5 min)
5. **Rotate Kaggle API key** committed in `.env`. (~5 min + key regeneration)
