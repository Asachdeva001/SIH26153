# SIH26153 — Cloud Training & Deployment Plan

**Audit Date:** 2026-09-23

## Changelog — Re-audit (frontend/backend split + cloud training)
- **New File:** Created to document the production-grade cloud training and deployment strategy for AWS/GCP, addressing data storage, compute, reproducible pipelines, security, and CI/CD.

---

## Executive Summary: Cloud & Production

| Area | Current State | Target State | Effort | Priority |
|---|---|---|---|---|
| **Cloud Infra (IaC)** | ❌ None (No Terraform/CloudFormation) | Terraform module for VPC, Storage, Compute | M | P1 |
| **Data & Artifacts** | ❌ Local `data/` and `models/` (excluded from git) | S3 (AWS) or GCS (GCP) buckets | S | P0 |
| **Compute (Training)** | ❌ Local execution | AWS `g4dn.xlarge` or GCP `n1-standard-4` + T4 | M | P1 |
| **Training Pipeline** | ❌ Missing `src/`, local script deleted | Containerized training job (`cloudbuild.yaml` or AWS Batch) | L | P1 |
| **Serving Handoff** | ❌ Manual file copy | Startup script pulls `latest` from S3/GCS | S | P0 |
| **Deployment Target** | ❌ No Dockerfiles (deleted) | Backend: ECS/Cloud Run. Frontend: Vercel/Amplify | M | P0 |
| **CI/CD** | ❌ None | GitHub Actions (Lint, Test, Build, Deploy) | M | P1 |

---

## 1. Current State Inventory
- **Codebase:** The project has been restructured into a FastAPI backend and a Next.js frontend. However, all Dockerfiles and deployment configurations (e.g., `render.yaml`, `Procfile`) were deleted in recent commits.
- **Training Scripts:** The `scripts/train.py` and core ML logic (`src/`) were accidentally deleted during the restructure. There is currently no cloud-specific code, Terraform, or boto3/gcsfs usage.
- **Artifacts:** Checkpoints (`.pth`, `.pkl`) were removed from git history to save space, but no remote storage mechanism was introduced.

---

## 2. Data & Artifact Storage
**Recommendation:** Use **Amazon S3** (or Google Cloud Storage).
- **Layout:**
  - `s3://ntro-sih26153-data/raw/` (CIC-IDS-2018 CSVs, PCAPs)
  - `s3://ntro-sih26153-data/processed/` (Windowed feature matrices)
  - `s3://ntro-sih26153-models/checkpoints/` (Mid-training weights)
  - `s3://ntro-sih26153-models/releases/` (Final `.pth`, `scaler.pkl`, `benchmark_report.json`)
- **Action:** Update the training script to use `fsspec` or `boto3` to read/write directly to S3. Do not rely on local relative paths for datasets in production.

---

## 3. Compute for Training
**Recommendation:** 
- **AWS:** `g4dn.xlarge` (1 T4 GPU, 4 vCPU, 16GB RAM) — ~ $0.52/hr on-demand, ~$0.15/hr Spot.
- **GCP:** `n1-standard-4` + 1 NVIDIA T4 — ~ $0.40/hr Spot.
**Reasoning:** The LSTM model is relatively small (~64k params), so a single T4 GPU is more than sufficient for fast training on the CIC-IDS-2018 dataset (358 MB per day file).
**Spot Instances:** Use Spot/Preemptible instances to reduce costs by 70%. Implement frequent checkpointing to S3 to survive preemption.
**Setup:** Use an AWS Deep Learning AMI (Ubuntu) to avoid manual CUDA/driver installation.

---

## 4. Reproducible Cloud Training Pipeline
To satisfy R10 (Reproducibility), training must be automated.
- **Implementation:** Create a `train_cloud.sh` script (or Makefile target).
- **Workflow:**
  1. Pull codebase and install dependencies.
  2. Download data from `s3://ntro-sih26153-data/raw/`.
  3. Run training: `python scripts/train.py --data-dir /tmp/data --epochs 35`.
  4. Evaluate against the test set.
  5. Upload artifacts (`world_model_v1.pth`, `scaler.pkl`, `metrics.json`) to `s3://ntro-sih26153-models/releases/<timestamp>-<commit_hash>/`.

---

## 5. Model → Serving Handoff
- **Mechanism:** The FastAPI backend should *not* bundle the model inside the Docker image (anti-pattern for large binaries).
- **Startup:** In `backend/main.py`'s `lifespan` event, the API should read a `manifest.json` from S3 (or accept an env var `MODEL_VERSION`), download the specific `.pth` and `.pkl` files to a local `/tmp/models` directory, and load them into memory.

---

## 6. Deployment Targets for Live Services
- **Backend (FastAPI):** Deploy to **AWS ECS Fargate** or **GCP Cloud Run**. 
  - *Compute:* CPU-only is sufficient for inference (K-step rollout takes <0.1s on CPU).
  - *Scaling:* Auto-scale based on CPU utilization.
- **Frontend (Next.js):** Deploy to **Vercel** or **AWS Amplify**.
- **CII / Offline Positioning Trade-off:** Deploying to public PaaS (Vercel/Cloud Run) contradicts the "fully offline / air-gapped" narrative (R17). For the enterprise SOC narrative, it is more authentic to deploy both containers to a single EC2 instance inside a private VPC, simulating an on-prem deployment.

---

## 7. Security for Cloud Environment
- **IAM:** Create dedicated roles. The training VM gets `S3ReadWrite`. The ECS backend gets `S3ReadOnly`.
- **Secrets:** Use AWS Secrets Manager or GCP Secret Manager for Kaggle API keys (used in data pipelines). NEVER commit `.env`.
- **Network:** 
  - Backend runs in a Private Subnet.
  - Expose API via an Application Load Balancer (ALB) in a Public Subnet with TLS (HTTPS) termination.

---

## 8. CI/CD Proposal
Use **GitHub Actions**:
- `lint-and-test.yml`: Runs on PR. Executes `pytest`, `eslint`, and `pip-audit`.
- `build-and-deploy.yml`: Runs on push to `main`. Builds Docker images and updates ECS/Cloud Run.
- `train-model.yml`: `workflow_dispatch` (manual trigger). Spins up a GPU runner (or submits an AWS Batch job) to execute `train_cloud.sh`.

---

## 9. Cost Guardrails
- **Lifecycle Rules:** Set S3 bucket policies to expire old mid-training checkpoints after 7 days.
- **Auto-shutdown:** Configure the training EC2 instance to terminate itself (`sudo shutdown -h now`) at the end of the `train_cloud.sh` script to prevent idle GPU billing.
- **Budgets:** Set an AWS Budget alert at $20/month.

---

## 10. Judging-Day Reality Check
**Recommendation: DO NOT rely on a live cloud environment for the primary SIH demo.**
- **Why:** Hackathon Wi-Fi is notoriously unreliable. A cloud demo introduces latency and risk, and contradicts the R17 offline requirement.
- **The Playbook:** 
  1. Train the model on AWS prior to the finale.
  2. Download the final weights to your laptop.
  3. Run the demo **fully locally** (`fastapi dev` + `bun dev` or local `docker-compose`) to prove it works air-gapped.
  4. Show the cloud pipeline scripts and CI/CD logs to the judges as proof of "Production Readiness".
