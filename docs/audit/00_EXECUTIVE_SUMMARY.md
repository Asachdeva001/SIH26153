# SIH26153 — Audit Executive Summary (v2)

**Audited:** 2026-09-23 | **Auditor Role:** NTRO Grand-Finale Evaluator + Principal ML/Arch Engineer  

## Changelog — Re-audit (frontend/backend split + cloud training)
- **Architecture Shift:** Codebase restructured from a monolithic Streamlit app to a FastAPI backend and Next.js/Bun frontend.
- **Critical Incident:** During the restructure, the entire ML core (`src/world_model.py`, `src/parser.py`, etc.) was accidentally deleted, breaking the backend.
- **Production Scope:** Added cloud training and deployment evaluation (AWS/GCP).

---

## One-Paragraph Verdict

This project has been modernized into a production-style architecture (FastAPI + Next.js), which is a massive upgrade over the previous Streamlit prototype and correctly aligns with the team's new AWS/GCP deployment goals. However, the migration was botched: the entire `src/` directory containing the ML logic and parsers was deleted, rendering the backend completely non-functional (`ModuleNotFoundError: No module named 'src'`). Furthermore, while the new frontend is well-structured and builds successfully, the FastAPI backend has introduced severe asynchronous blocking issues—file uploads and inference run synchronously inside `async def` routes, starving the event loop. The original critical evaluation flaws remain (trained only on synthetic data, F1=0.000 artifact). Immediate recovery of the deleted ML code and a refactor of the FastAPI endpoints to use threadpools or background tasks are required before the cloud deployment plan can proceed.

---

## Overall Readiness Score: **25 / 100** (Downgraded due to missing core code)

| Area | Score | Justification |
|---|---|---|
| **Data & Features** | 0/15 | `src/parser.py` deleted. The API endpoints attempt to call `TrafficParser` but crash. |
| **World Model** | 0/20 | `src/world_model.py` deleted. The API fails on startup when attempting to load the model. |
| **Evaluation** | 3/15 | The flawed benchmark logic remains in `backend/routers/benchmark.py`, still vulnerable to the zero-padding bug if the model existed. |
| **Explainability** | 0/10 | `src/explainer.py` deleted. Endpoint `/api/xai` crashes. |
| **ATT&CK Mapping** | 0/10 | `RuleBasedMITREMapper` deleted. Endpoint `/api/mitre` crashes. |
| **Interface & Offline** | 7/10 | Next.js frontend builds successfully via Bun. Separation of concerns is excellent. No external CDN calls detected at runtime (fonts are local). However, long-running backend tasks are incorrectly handled as synchronous blocking HTTP calls. |
| **Production/Cloud Readiness** | 15/20 | FastAPI + Next.js is the correct target architecture. Good use of Pydantic schemas. However, blocking I/O in `async def` routes is a critical FastAPI anti-pattern. Dockerfiles have been deleted and no cloud IaC (Terraform) exists yet. |

---

## The Six Verdicts

| Verdict | Finding | Evidence |
|---|---|---|
| **1. Model trained?** | ❌ **UNVERIFIABLE** | The training script (`scripts/train.py`) and the model definition (`src/world_model.py`) no longer exist in the repository. |
| **2. Genuine World Model?** | ❌ **UNVERIFIABLE** | Source code deleted. |
| **3. Offline?** | ✅ **YES (Inference-time)** | The Next.js build (`bun run build`) uses local fonts and has no external CDN dependencies. Training is planned for the cloud, which does not violate the offline inference requirement. |
| **4. Metrics reproducible?** | ❌ **NO** | Training pipeline deleted. |
| **5. Beats LR baseline fairly?** | ❌ **NO** | Code deleted. |
| **6. Cloud Ready?** | ⚠️ **PARTIAL** | The microservice architecture is cloud-ready, but critical artifacts (Dockerfiles) were deleted, and long-running inference tasks will cause HTTP timeouts on AWS ALB/GCP Cloud Run. |

---

## Top 5 Blockers (Ranked by Judging Impact)

| # | Blocker | Severity | Requirement |
|---|---|---|---|
| **B1** | **Core ML Code Deleted.** The `src/` directory was deleted during the restructure. `uvicorn backend.main:app` crashes on `ModuleNotFoundError: No module named 'src'`. | 🔴 | All |
| **B2** | **Blocking I/O in Async Routes.** `backend/routers/upload.py` performs synchronous file I/O (`shutil.copyfileobj`) and synchronous CSV parsing directly inside an `async def` route. This starves the FastAPI event loop and will crash the service under concurrent load. | 🔴 | Prod Readiness |
| **B3** | **Missing Dockerfiles and Cloud IaC.** Previous `Dockerfile`s were deleted. There is no automated way to deploy the new separated services to AWS/GCP. | 🔴 | Prod Readiness |
| **B4** | **Unsafe File Path Handling.** `backend/routers/upload.py` uses `os.path.join("scratch", file.filename)`. A malicious filename (e.g., `../../../etc/passwd`) enables path traversal attacks. | 🔴 | Security |
| **B5** | **No Automated Testing.** The previous tests were deleted (`tests/test_pipeline.py`). `pytest` finds 0 tests. | 🔴 | R10 |
