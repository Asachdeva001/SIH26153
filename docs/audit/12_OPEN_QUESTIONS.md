# SIH26153 — Open Questions (v2)

**Audit Date:** 2026-09-23

## Changelog — Re-audit (frontend/backend split + cloud training)
- Removed questions related to Streamlit architecture.
- Added questions specifically regarding the cloud environment, infrastructure provisioning, and judging-day logistics.

---

## 1. Cloud & Infrastructure Decisions

| Question | Context | Impact | Owner Needed |
|---|---|---|---|
| **AWS vs. GCP?** | We need to select a primary cloud provider for the training pipeline and IaC (Terraform). | Defines the CI/CD pipeline and IAM permissions model. | Team Lead |
| **Who holds the Cloud Credentials?** | A dedicated service account is needed for GitHub Actions to push models to S3/GCS. | Security risk if personal accounts are used. | SecOps |
| **Are we doing a Live Cloud Demo?** | The codebase supports local deployment. A live cloud demo introduces latency and WiFi dependency risks. | A live cloud demo breaks R17 (offline). We must decide if the "wow factor" is worth the risk. | Architect |

## 2. Recovery & Data

| Question | Context | Impact | Owner Needed |
|---|---|---|---|
| **Where is the `src/` directory?** | Commit `008719d` deleted `src/`. Was it moved to a private submodule, or accidentally deleted? | High. The backend is completely broken without it. | Author (`8dae065`) |
| **Will we train on the full 10-day dataset?** | Training currently (before deletion) used a single 358MB CSV. | High. Multi-day training requires GPU compute and a multi-file parser update. | ML Engineer |

## 3. Product & UX

| Question | Context | Impact | Owner Needed |
|---|---|---|---|
| **What is the max upload size limit?** | FastAPI currently has no `LimitRequestBody` configured. | High. A user uploading a 2GB PCAP will OOM the container. | Backend Dev |
| **Do we need WebSockets for the UI?** | File uploads currently block the HTTP response until parsing is complete. | Medium. Long HTTP requests will timeout on Cloud Run / ALB (usually 30s-60s limit). | Full-Stack Dev |
