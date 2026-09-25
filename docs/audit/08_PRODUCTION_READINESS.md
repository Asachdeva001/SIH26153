# SIH26153 — Production Readiness Audit (v2)

**Audit Date:** 2026-09-23

## Changelog — Re-audit (frontend/backend split + cloud training)
- **Frameworks:** Completely rewritten to audit FastAPI (Backend) and Next.js/Bun (Frontend).
- **Missing Artifacts:** Dockerfiles, CI pipelines, and ML code were deleted and are flagged as critical blockers.
- **Async Pitfalls:** Audited FastAPI asynchronous correctness and event loop starvation.

---

## 1. Backend (FastAPI) Production Audit

| Area | Status | Findings |
|---|---|---|
| **API Design** | ✅ | Clean separation into feature routers (`upload.py`, `forecast.py`). Proper use of HTTP verbs (POST for uploads/computation, GET for scenario). |
| **Pydantic Validation** | ✅ | Excellent typing in `backend/schemas/requests.py` mapping exactly to expected ML types. |
| **Async Correctness** | 🔴 BLOCKER | `upload_file` is defined as `async def` but executes blocking file I/O (`shutil.copyfileobj`) and ML parsing (`parser.parse_csv`) directly. **This starves the ASGI event loop.** Standard CPU-bound endpoints (e.g. `/api/forecast`) correctly use `def` to offload to the threadpool, but `/api/xai` contains heavy GPU/CPU workloads that will cause GIL contention. |
| **Model Loading** | ✅ | Models are loaded once at startup via `@app.on_event("startup")` and reused via FastAPI `Depends()`. |
| **Concurrency Config** | ❌ | No `gunicorn` or multi-worker `uvicorn` configuration provided for production scaling. |
| **Testing** | 🔴 BLOCKER | `tests/` directory was deleted. No test coverage exists. |
| **Dockerization** | 🔴 BLOCKER | `Dockerfile` was deleted. |
| **CORS Configuration** | 🟠 HIGH | `allow_origins=["*"]` in `main.py:31` is unsafe for production. Must be locked down to the frontend domain. |
| **Configuration** | ❌ | No `.env` parsing via `pydantic-settings`. Hardcoded paths (`"scratch/"`, `"models/"`). |

---

## 2. Frontend (Next.js + Bun) Production Audit

| Area | Status | Findings |
|---|---|---|
| **Structure** | ✅ | Clean App Router structure (`src/app/`). Client-side state managed correctly with React hooks. |
| **API Integration** | ✅ | `API_BASE_URL` is environment-driven via `NEXT_PUBLIC_API_URL` (`lib/api.ts`). |
| **Bun Compatibility** | ✅ | `bun.lock` exists (116KB). Run `bun install && bun run build` succeeded locally in 29.9s. |
| **Type Safety** | ⚠️ Partial | `lib/types.ts` is hand-written to match FastAPI schemas. Risk of drift. Consider `openapi-typescript` generator for CI/CD. |
| **Build Artifact** | ✅ | Compiles to a static Node/Bun production bundle successfully. |

---

## 3. Security & Vulnerability Checklist

| Item | Status | Fix Required |
|---|---|---|
| **Path Traversal via Upload** | 🔴 CRITICAL | `backend/routers/upload.py:12` uses `os.path.join("scratch", file.filename)`. Must sanitize using `os.path.basename()` or `secure_filename`. |
| **Missing Secrets Management** | 🔴 CRITICAL | Kaggle API credentials were removed from `.env` in history but no cloud-secret mechanism was established. |
| **DDoS via File Upload** | 🟠 HIGH | No max upload size limit configured in FastAPI. A 10GB CSV will crash the container via OOM. |
| **Rate Limiting** | 🟠 HIGH | No `slowapi` or rate limiting on computationally expensive endpoints like `/api/xai`. |

---

## 4. Technical Debt Register (Updated)

| Item | File | Severity | Effort | Notes |
|---|---|---|---|---|
| **Restore ML Core** | `src/` | 🔴 CRITICAL | M | Undelete `src/world_model.py`, `src/parser.py`, `src/explainer.py`. |
| **Fix Async File I/O** | `upload.py:10` | 🔴 CRITICAL | S | Wrap `shutil.copyfileobj` and `parse_csv` in threadpool or use asynchronous file libraries. |
| **Sanitize Upload Path** | `upload.py:12` | 🔴 CRITICAL | S | Implement `os.path.basename(file.filename)`. |
| **Add CI/CD Tests** | `tests/` | 🔴 CRITICAL | M | Restore `test_pipeline.py` and add API client tests using `TestClient`. |
| **Create Dockerfiles** | Root | 🔴 CRITICAL | S | Need multi-stage Dockerfiles for both Backend and Frontend. |
| **Lock CORS Origins** | `main.py:31` | 🟠 HIGH | S | Replace `["*"]` with environment variable `FRONTEND_URL`. |
| **Add File Size Limit** | `upload.py` | 🟠 HIGH | S | Read `Content-Length` header and reject if > 500MB. |
| **Auto-generate OpenAPI clients** | `frontend/` | 🟡 MED | M | Replace manual `lib/types.ts` with auto-generated schema from `/openapi.json`. |
