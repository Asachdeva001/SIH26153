# SIH26153 — Prioritised Action Plan (v2)

**Audit Date:** 2026-09-23  
**Purpose:** Roadmap to recover from the botched restructure and deliver a production-grade cloud ML system.

---

## P0 — CRITICAL RECOVERY & INFRASTRUCTURE (Fix Immediately)

| ID | What | Why | Where | How | Acceptance Criteria | Effort |
|---|---|---|---|---|---|---|
| **P0-1** | **Restore ML Core (`src/`)** | Backend is entirely broken (`ModuleNotFoundError`). | `src/` directory | Retrieve `src/world_model.py`, `src/parser.py`, `src/explainer.py`, and `src/synthetic_generator.py` from commit `8dae065`. | `uvicorn backend.main:app` starts successfully. | S |
| **P0-2** | **Fix Async Event Loop Starvation** | Uploading files freezes the FastAPI server. | `backend/routers/upload.py` | Change `async def upload_file` to `def upload_file` OR wrap `shutil.copyfileobj` and `parser.parse_csv` in `anyio.to_thread.run_sync()`. | App handles concurrent requests during a large CSV upload. | S |
| **P0-3** | **Fix Path Traversal Vulnerability** | Security. | `backend/routers/upload.py` | Change `os.path.join("scratch", file.filename)` to use `os.path.basename()`. | Malicious filenames are sanitized. | S |
| **P0-4** | **Rebuild Cloud Training Script** | Missing `train.py`. Required for AWS/GCP pipeline. | `backend/scripts/train_cloud.py` | Restore old script, add `boto3` or `gcsfs` to pull CIC-IDS-2018 from S3/GCS, and push weights back to S3. | Script runs on a cloud VM and produces `.pth` in S3. | M |
| **P0-5** | **Create Dockerfiles** | Needed for ECS/Cloud Run deployments. | `backend/Dockerfile`, `frontend/Dockerfile` | Write multi-stage Dockerfiles. Expose 8000 (FastAPI) and 3000 (Next.js). | `docker-compose up` runs the full stack locally. | M |

---

## P1 — HIGH (Evaluation Rigour & Cloud CI/CD)

| ID | What | Why | Where | How | Acceptance Criteria | Effort |
|---|---|---|---|---|---|---|
| **P1-1** | **Fix label engineering for real CIC-IDS-2018** | Risk head trains on all-zeros without this. | `train_cloud.py`, `src/world_model.py` | Map `Label` column to a 0.0-1.0 risk score before passing to `fit()`. | Model outputs risk > 0.6 for attacks. | M |
| **P1-2** | **Fix train/test split for single-CSV scenario** | Grouped split collapses with 1 file. | `train_cloud.py` | Implement temporal split by timestamp quintile for single files. | `len(train_df) > 0` | S |
| **P1-3** | **Train world model on AWS/GCP** | The current prototype only uses synthetic data. | AWS EC2 / GCP VM | Provision VM, run `train_cloud.py` on real CSV, download final artifact. | Real metrics generated. | M |
| **P1-4** | **Fix broken benchmark evaluation** | Padding WM probs with zeros inflates FP. | `train_cloud.py` | Implement K-horizon evaluation loop (`05_EVALUATION_AND_BENCHMARKS.md`). | F1 score > 0. | M |
| **P1-5** | **Set up GitHub Actions (CI/CD)** | Professional standard. | `.github/workflows/` | Create workflows for lint, test, and docker build. | Badges show passing. | M |
| **P1-6** | **Restore automated tests** | Zero tests currently exist. | `tests/` | Restore `test_pipeline.py`. Add `httpx` tests for FastAPI routes. | >80% coverage. | M |

---

## P2 — MEDIUM (UX & Robustness)

| ID | What | Why | Where | How | Acceptance Criteria | Effort |
|---|---|---|---|---|---|---|
| **P2-1** | **Add Upload Progress Bar & Limits** | 1GB files will timeout. | `upload.py`, Next.js UI | Enforce Max Content-Length. (Optional: implement chunking/job ID polling). | UI handles large files gracefully. | M |
| **P2-2** | **Remove `["*"]` from CORS** | Security. | `backend/main.py` | Map to `NEXT_PUBLIC_FRONTEND_URL`. | Secure origin. | S |
| **P2-3** | **Implement PCAP Retransmission Detection** | Honest feature reporting. | `src/parser.py` | Parse TCP sequence/ack numbers via Scapy to count retransmissions. | PCAPs populate accurate counts. | M |

---

## Minimum Winning Path (Hackathon Timeline)

### Day 1: Code Recovery & Infra
1. **P0-1:** Undelete `src/` directory.
2. **P0-2 & P0-3:** Fix FastAPI async blocks and path traversal.
3. **P0-5:** Write Dockerfiles and `docker-compose.yml`.

### Day 2: Cloud Training & ML Fixes
4. **P0-4:** Write `train_cloud.py`.
5. **P1-1 & P1-2 & P1-4:** Fix the data labeling, splitting, and benchmarking logic.
6. **P1-3:** Spin up AWS/GCP VM, pull CIC-IDS-2018, train overnight.

### Day 3: UI Integration & Presentation
7. Hook up new real model to the backend.
8. Verify Next.js renders everything correctly (Benchmark tab, Timeline).
9. Record local air-gapped demo video showing inference.

---

## 2-Minute Demo Script (Updated for v2 Architecture)

| Time | Action | Key Talking Point |
|---|---|---|
| 0:00–0:15 | Show GitHub Actions / Cloud pipeline logs. | "We trained the world model on AWS using petabytes of flow data." |
| 0:15–0:30 | Switch to local browser (`localhost:3000`). | "But for inference in the SOC, we deploy a lightweight, fully air-gapped Next.js + FastAPI stack." |
| 0:30–0:55 | Upload real PCAP/CSV. | "Dual input parses raw packets or NetFlow CSVs securely on-premise." |
| 0:55–1:15 | Show Forecast Timeline diverging. | "The model autoregressively simulates 5 steps into the future, predicting attack escalation." |
| 1:15–1:40 | Explainability (XAI). | "GradientShap explains *why* the LSTM flagged it. No black boxes." |
| 1:40–2:00 | SOC Playbook. | "One-click mitigation playbooks for the human analyst." |
