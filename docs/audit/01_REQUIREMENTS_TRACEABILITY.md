# SIH26153 — Requirements Traceability Matrix

**Audit Date:** 2026-09-23

## Changelog — Re-audit (frontend/backend split + cloud training)
- Updated paths to reflect the new FastAPI (`backend/`) and Next.js (`frontend/`) architecture.
- Marked ML/training requirements as ❌ Missing because the `src/` directory and `scripts/train.py` were deleted in recent commits.
- Refined R17 (Offline) to clarify that cloud-based training is acceptable; inference is fully offline.

---

| ID | Requirement | Status | Evidence Location (Code/File) | Verdict Details / Gaps | Fix Action Required | Effort | Severity |
|---|---|---|---|---|---|---|---|
| **R1** | Ingest raw PCAP and/or CSV telemetry | ⚠️ Partial | `backend/routers/upload.py:10` [READ] accepts file uploads, but relies on deleted `src/parser.py`. | API endpoint exists but core parser is missing. | Restore `TrafficParser` and wrap synchronous I/O in `run_in_threadpool`. | S | 🔴 |
| **R2** | Produce timestamped normalised feature matrix | ❌ Missing | Missing `src/parser.py`. | Code deleted. | Restore code. | S | 🔴 |
| **R3** | Extract flow-level features (duration, size, inter-arrival, etc.) | ❌ Missing | Missing `src/parser.py`. | Code deleted. | Restore code. | S | 🔴 |
| **R4** | Extract packet-level features (TTL, window sizes, flags) | ❌ Missing | Missing `src/parser.py`. | Code deleted. | Restore code. | S | 🔴 |
| **R5** | Accommodate both extraction levels in model | ❌ Missing | Missing `src/world_model.py`. | Code deleted. | Restore code. | S | 🔴 |
| **R6** | Transform raw series into global time windows | ❌ Missing | Missing `src/parser.py`. | Code deleted. | Restore code. | S | 🔴 |
| **R7** | Unsupervised/Self-Supervised World Model learning | ❌ Missing | Missing `src/world_model.py`. | Code deleted. | Restore code. | S | 🔴 |
| **R8** | Handle multi-stage / APT data characteristics | ❌ Missing | Missing `scripts/train.py`. | Code deleted. | Restore code. | S | 🔴 |
| **R9** | Test generalisation across attack scenarios | ❌ Missing | Missing `scripts/train.py`. | Code deleted. | Restore code. | S | 🔴 |
| **R10**| Replicable training pipeline (seeds, splits, logs) | ❌ Missing | Missing `scripts/train.py`. | Code deleted. | Restore code & containerize training pipeline for cloud. | M | 🔴 |
| **R11**| K-step forward simulation from traffic snapshot | ❌ Missing | Missing `src/world_model.py`. API endpoint `backend/routers/forecast.py` exists but cannot run. | Code deleted. | Restore code. | S | 🔴 |
| **R12**| Return $K$ infiltration probability values (time-series) | ⚠️ Partial | `backend/routers/forecast.py` returns `risk_trajectory`. Next.js `frontend/src/app/components/tabs/ForecastTimeline.tsx` renders it. | UI and API exist, but model is missing. | Restore model. | S | 🔴 |
| **R13**| Return predicted ATT&CK stage/tactic | ⚠️ Partial | `backend/routers/mitre.py` and `frontend/src/app/components/tabs/MitreTracker.tsx`. | UI and API exist, mapper deleted. | Restore mapper. | S | 🔴 |
| **R14**| Return feature attribution / confidence score | ⚠️ Partial | `backend/routers/xai.py` and `frontend/src/app/components/tabs/XaiAttribution.tsx`. | UI and API exist, explainer deleted. | Restore explainer. | S | 🔴 |
| **R15**| Interface for evaluator inputs (PCAP/CSV upload) | ✅ Met | `frontend/src/app/components/layout/ControlPanel.tsx:55` [READ]. | Next.js frontend handles file uploads cleanly. | None | — | 🟢 |
| **R16**| Real-time trajectory plotting, flagged flows, explanations | ✅ Met | `frontend/src/app/dashboard/page.tsx` [READ]. | All required visualizations are built in React. | None | — | 🟢 |
| **R17**| Runs fully offline, zero cloud-API dependencies | ✅ Met | `bun run build` [RUN] produced a static/standalone bundle with no external font or CDN calls. | **Inference is offline-safe.** Training in AWS/GCP does not violate this. | None | — | 🟢 |
| **R18**| Compare World Model against a standard static baseline | ⚠️ Partial | `backend/routers/benchmark.py` exists, but uses flawed logic and missing evaluator. | Model/Evaluator deleted. | Restore code and fix evaluation logic. | M | 🔴 |
| **R19**| Metric: Lead Time (temporal advantage over baseline) | ⚠️ Partial | `frontend/src/app/components/tabs/Benchmark.tsx` exists. | Model/Evaluator deleted. | Restore code. | M | 🔴 |
| **R20**| Target enterprise environments/CII (Playbooks, Assets) | ✅ Met | `backend/routers/soc.py` + `frontend/src/app/components/tabs/SocResponse.tsx`. | Well-designed SOC priority UI. | None | — | 🟢 |
| **R21**| Submit under open-source license | ❌ Missing | No `LICENSE` file found. | Missing. | Add MIT or Apache-2.0 LICENSE file. | S | 🟡 |
| **R22**| Upload complete source code repository | ⚠️ Partial | Pushed to GitHub, but `src/` directory accidentally deleted. | Incomplete source. | Restore `src/`. | S | 🔴 |
| **R23**| Provide detailed README with setup instructions | ❌ Missing | `README.md` was significantly truncated and no longer contains setup instructions. | Useless README. | Rewrite README for FastAPI+Next.js. | S | 🔴 |
| **R24**| Submit Architecture/System Design Document | ❌ Missing | Not present. | Missing. | Write architecture doc. | S | 🔴 |
| **R25**| Submit 2-min demo video (YouTube/Vimeo) | ❌ Missing | Not present. | Missing. | Record and link video. | S | 🔴 |
| **R26**| Submit max 5 slide presentation | ❌ Missing | Not present. | Missing. | Create slides. | S | 🔴 |
