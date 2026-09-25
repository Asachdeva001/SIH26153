# SIH26153 — Developer Onboarding Guide (v2)

**Audit Date:** 2026-09-23

## Changelog — Re-audit (frontend/backend split + cloud training)
- Complete rewrite for the new separated repository structure (FastAPI + Next.js).
- Swapped npm/yarn commands for Bun commands.
- Added cloud training execution instructions.

---

## 1. Project Structure

The project is split into two microservices:

1. **`backend/`**: A FastAPI application serving the ML endpoints (PyTorch, Captum, Scapy).
2. **`frontend/`**: A Next.js 15 (App Router) client managed by Bun.
3. **`src/`**: **(CURRENTLY DELETED - MUST BE RESTORED)** The shared ML core used by the backend.

---

## 2. Local Setup (Development)

### Prerequisites
- Python 3.10+
- [Bun](https://bun.sh/) 1.4+
- `libffi-dev` / `libpcap-dev` (for Scapy packet parsing)

### A. Clone and Restore
```bash
git clone https://github.com/[org]/SIH26153.git
cd SIH26153
# CRITICAL: You must checkout the commit before src/ was deleted or manually restore it.
git checkout 8dae065 -- src/
```

### B. Setup Backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e ..  # Install the root `src` package in editable mode

# Run the dev server
fastapi dev main.py --port 8000
```
*API Docs available at http://localhost:8000/docs*

### C. Setup Frontend (Next.js)
```bash
# In a new terminal
cd frontend
bun install
bun run dev
```
*App available at http://localhost:3000*

---

## 3. Cloud Training (AWS/GCP)

*(Optional for local development. Required for production model updates).*

1. Provision an AWS `g4dn.xlarge` instance (Deep Learning AMI).
2. SSH into the instance and clone the repo.
3. Download the dataset:
   ```bash
   aws s3 cp s3://ntro-sih26153-data/raw/02-14-2018.csv /tmp/data/
   ```
4. Run the training script:
   ```bash
   python backend/scripts/train_cloud.py --data-dir /tmp/data
   ```
5. The script will automatically push `world_model_v1.pth` and `scaler.pkl` to the S3 bucket upon completion.

---

## 4. Key Developer Gotchas
- **Event Loop Starvation:** Never use blocking I/O (like `open()` or heavy pandas processing) directly inside an `async def` route in FastAPI. Either use `def` (which FastAPI runs in a threadpool) or use `await anyio.to_thread.run_sync()`.
- **Bun Workspaces:** Currently, the frontend is a standalone Bun project, not a monorepo workspace. Do not run `bun install` in the root directory.
- **Model Paths:** The `backend/models/loader.py` expects models to be in `backend/models/`. Ensure you copy newly trained models there before running the backend.
