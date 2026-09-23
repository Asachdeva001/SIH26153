# SIH26153 — Audit Executive Summary

**Audited:** 2026-09-21 | **Auditor Role:** NTRO Grand-Finale Evaluator + Principal ML/Arch Engineer  
**Repository:** `c:\Users\karrt\.vscode\SIH26` (8 commits, 1 author)

---

## One-Paragraph Verdict

This prototype is a **competently assembled, partially honest SIH-26153 submission** that has real code, a real trained LSTM checkpoint (`world_model_v1.pth`), a working Streamlit UI, a PCAP+CSV dual parser, a Captum GradientShap explainability engine, and all 9 automated tests passing. However, it has **critical architectural and evaluation integrity problems** that would be immediately spotted by a knowledgeable NTRO evaluator: (1) the saved model was **trained exclusively on synthetically generated data**, not on CIC-IDS-2018/CTU-13, despite the repository containing the real CSV; (2) the benchmark report in `models/benchmark_report_synthetic.json` shows **World Model F1 = 0.000** versus Baseline F1 = 0.982 — the world model *loses* comprehensively in the saved artifact, an embarrassing negative result caused by a fundamentally broken evaluation methodology (benchmarking K-step rollout scores against current-window ground truth); (3) the ATT&CK stage mapping is fully **rule-based, not forecasted**, contradicting the core claim; (4) there is a **live CDN dependency** (Google Fonts) violating the offline requirement R17; (5) the KAGGLE API key is committed in `.env` and tracked in history.

---

## Overall Readiness Score: **42 / 100**

| Area | Score | Justification |
|---|---|---|
| **Data & Features** | 7/15 | Real CSV exists (358 MB, CIC-IDS-2018). PCAP parser genuine. But packet-level features (TTL, tcp_win, ip_frag, retrans) are **zero-filled defaults** when reading flow CSVs — not extracted from real packets. |
| **World Model** | 8/20 | LSTM architecture is genuine. Dual-head (state decoder + risk head) design is correct. K-step rollout is truly autoregressive. BUT: weights trained only on synthetic data. Risk scores on very different inputs (benign vs attack) differ by only 0.011 — model discriminates poorly. |
| **Evaluation** | 3/15 | Saved benchmark shows WM F1=0.000. No temporal/chronological test split was used when the real CSV was parsed. No per-horizon metrics, no calibration, no cross-dataset test. |
| **Explainability** | 7/10 | Captum GradientShap genuinely wired to the deployed model. Per-sample. Named features. Narrative generation. Passes sanity test. |
| **ATT&CK Mapping** | 4/10 | All 5 stages present. MITRE IDs correct. BUT mapping is hard-coded rule table on the *current* state vector, not the *forecasted* future state. Partially contradicts R13. |
| **Interface & Offline** | 4/10 | Streamlit UI functional, 8 tabs, PCAP+CSV upload works. **🔴 Google Fonts CDN call at app.py:26 violates R17.** Benchmark tab uses hard-coded 3.5 in the bar chart regardless of input (app.py:856). |
| **Production Readiness** | 5/10 | 9/9 tests pass. Chronological split logic correct. No CI pipeline. Kaggle API key committed in `.env`. No pinned versions. `torch.load(weights_only=False)` unsafe. |
| **Deliverables** | 4/10 | No architecture doc (R24). No demo video (R25). No slide deck (R26). README exists but Kaggle credentials required at setup. |

---

## The Five Verdicts

| Verdict | Finding | Evidence |
|---|---|---|
| **1. Model trained?** | ⚠️ **TRAINED BUT ON SYNTHETIC DATA ONLY** | `benchmark_report_synthetic.json:2` says `"dataset": "Synthetic Dev/CI Fallback"`. `train.py:50-76` shows real CSV path checked but `.gitignore:52` excludes all `data/` — so CI/CD never sees the real file. Real CSV present locally (`data/raw/ids-intrusion-csv/02-14-2018.csv`, 358 MB) but model saved from a synthetic run dated `2026-09-08T23:05:59`. [READ] |
| **2. Genuine World Model?** | ⚠️ **PARTIAL** — Architecture correct but discriminative learning very weak | Rollout is autoregressive (world_model.py:191-207 [READ]). Dual-head loss exists (line 118). But benign vs. attack inputs yield risk scores 0.7388 vs 0.7499 — gap of 0.011 [RUN]. Model essentially collapses to a near-constant output. |
| **3. Offline?** | ❌ **NO** — CDN dependency present | `app.py:26` [READ]: `@import url('https://fonts.googleapis.com/css2?...')` loaded in every browser session. |
| **4. Metrics reproducible?** | ❌ **NO** | Saved benchmark shows F1=0.000 for World Model — this is the artifact that ships. No `benchmark_report.json` for real dataset exists. Metrics in README ("+3.5 windows lead time") come from the broken synthetic evaluation. |
| **5. Beats LR baseline fairly?** | ❌ **NO** | Saved result: WM F1=0.000, Baseline F1=0.982. The **baseline wins by 98 percentage points**. The benchmark tab hard-codes `3.5` in the bar chart (app.py:856) to fabricate a lead-time advantage. |

---

## Top 10 Blockers (Ranked by Judging Impact)

| # | Blocker | Severity | Requirement |
|---|---|---|---|
| **B1** | **World Model trained on synthetic data only.** Real 358 MB CSV is present but the saved `.pth` checkpoint comes from the synthetic training run. Judges who run `python scripts/train.py` will get the correct path, but the *committed* model is fake. | 🔴 | R1, R8, R10 |
| **B2** | **Benchmark shows WM F1=0.000 — negative result committed.** The evaluation methodology is broken: K-step future risk scores are compared against *current-window* ground truth labels, which is meaningless. The UI bar chart hard-codes 3.5 to hide this. | 🔴 | R18, R19 |
| **B3** | **Google Fonts CDN call at `app.py:26` violates R17 (fully offline).** Without network, UI fonts fall back to system fonts but the CSS import still blocks. | 🔴 | R17 |
| **B4** | **Kaggle API credentials committed to `.env`** (`KAGGLE_USERNAME`, `KAGGLE_KEY`). The `.gitignore` excludes `.env` but the file already exists in the working tree and credentials are real. | 🔴 | Security |
| **B5** | **ATT&CK stage mapping is rule-based on current state, not forecasted future state.** The function `RuleBasedMITREMapper.map_state_to_stage()` takes the *current* window telemetry, not the simulated future state. This partially contradicts R13. | 🔴 | R13 |
| **B6** | **Packet-level features (TTL, tcp_win, ip_frag, retrans_count) are zero-filled from defaults when CSV input is used.** CIC-IDS-2018 flow CSVs don't contain these columns; `_ensure_column` silently fills them with constants (parser.py:105-109). R4 partially faked. | 🔴 | R4, R5 |
| **B7** | **No architecture document (R24), no demo video (R25), no presentation slides (R26).** Three submission deliverables are entirely missing. | 🔴 | R22-R26 |
| **B8** | **`torch.load(weights_only=False)` on user-uploaded file paths.** If a user uploads a malicious `.pth` file, arbitrary code executes. | 🔠 HIGH | Security, R17 |
| **B9** | **No temporal/chronological evaluation on the real CIC-IDS-2018 dataset.** The `grouped_chronological_split` is implemented but was never run on real data; the real CSV is 358 MB of a single day's data which cannot be split by "campaign". R9 unverifiable. | 🟠 | R8, R9, R18 |
| **B10** | **No CI pipeline** (.github/workflows missing). Tests pass locally but there's no automated enforcement. The README instruction requires Kaggle credentials to reproduce the real model. | 🟡 | R10, R23 |

---

## "If Judges Run This Tomorrow, What Would Break?"

1. **`streamlit run app.py`** — Loads with fonts broken (offline) or flickering (online). The model silently loaded is trained on synthetic data. The benchmark tab shows a hard-coded `3.5` bar regardless of actual forecast.
2. **`python scripts/train.py`** — Would train on real CSV (358 MB file present) this time, producing a `benchmark_report.json` with *real* numbers — but judges won't know the committed model differs.
3. **Upload a real CIC-IDS CSV** — TTL, tcp_window, ip_frag, retrans features silently default to 0/64240/0/0, corrupting predictions. No error or warning shown.
4. **Upload a PCAP** — Works if Scapy is installed, but IAT values are populated per-packet not per-flow (stub values: flow_iat_mean=0.01, constant for all packets), producing incorrect IAT statistics.
5. **Disconnect from internet, run app** — Google Fonts import causes slow page load; functionality is preserved but judges trying to demonstrate offline operation will see a delay.
6. **Ask about benchmark numbers** — The bar chart shows a hard-coded 3.5 windows lead-time advantage. Clicking through to the actual stored benchmark report reveals WM F1 = 0.0.

---

## Estimated Total Effort to Reach Target State

| Task Group | Effort |
|---|---|
| P0: Retrain on real CIC-IDS-2018, fix evaluation methodology, fix CDN, rotate secrets | **M (3–5 person-days)** |
| P1: ATT&CK from forecast, proper metrics, explainability sanity, clean benchmark | **M (3–5 person-days)** |
| P2: Architecture doc, demo video, slides, CI, Docker test | **S (1–2 person-days)** |
| P3: PCAP IAT fix, packet-level feature honest reporting, streaming | **L (5–8 person-days)** |
| **Total** | **~14–20 person-days (XL for a solo developer, M for a 3-person team)** |
