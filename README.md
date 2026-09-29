# Predictive Cyber Defense & SOC World Model

An explainable cyber-defense prototype that forecasts how network risk may evolve over time and helps a SOC analyst decide what to investigate first.

> **New here?** Use [Quick Start](#quick-start) to launch the complete website, then follow [How to Use the Website](#how-to-use-the-website).

The system connects four steps in one workflow:

```text
Network telemetry -> Future risk forecast -> MITRE/XAI explanation -> SOC priority and playbook
```

## Why this project

Traditional detection tells a defender what looks suspicious **now**. This project adds a temporal layer: it learns recent network behavior, predicts the next `K` network states, explains the main risk drivers, and prioritizes the response using asset criticality.

## What is implemented

- Synthetic scenarios for APT, ransomware, DDoS/C2 and benign traffic.
- CSV/PCAP upload and traffic windowing.
- 10-second network state windows with 25 engineered features.
- PyTorch two-layer LSTM World Model.
- K-step future state and risk forecasting.
- MITRE ATT&CK stage mapping.
- Captum GradientShap feature attribution and narrative explanation.
- Asset-aware P1-P4 SOC prioritization with SLA and playbook.
- Forecast, MITRE, XAI, K-step, SOC, benchmark, topology and audit views.
- Docker Compose deployment for local demonstration.

## Quick Start

The Docker workflow is the recommended way to run the full application because it starts the FastAPI backend and Next.js frontend with matching dependencies.

### Prerequisites

- Git
- Docker Desktop with Docker Compose v2
- At least 8 GB RAM recommended for the complete stack
- Ports `3000` and `8000` available

Verify Docker before continuing:

```bash
docker --version
docker compose version
```

### 1. Clone the repository

```bash
git clone https://github.com/<your-account>/<your-repository>.git
cd SIH26
```

Replace the clone URL with the repository URL shown on GitHub. If you downloaded a ZIP instead, extract it and open a terminal in the extracted `SIH26` folder.

### 2. Build and start the complete website

From the repository root:

```bash
docker compose up --build
```

The first build downloads the backend ML dependencies and builds the Next.js frontend, so it can take several minutes. Keep this terminal open while using the website. For later runs, use `docker compose up` unless source or dependency files changed.

### 3. Open the services

- **SOC dashboard:** http://localhost:3000
- **Backend health check:** http://localhost:8000/healthz
- **Interactive API documentation:** http://localhost:8000/docs

The health check should return a response containing:

```json
{"status":"ok","model_loaded":true}
```

If the dashboard loads but shows a backend connection error, wait for the health check to return `model_loaded: true`, then refresh http://localhost:3000.

### Stop the application

```bash
docker compose down
```

To remove the local model volume as well:

```bash
docker compose down -v
```

## Recommended 3-Minute Demo

### 1. Start with the default scenario

Open the dashboard. The default data source is the synthetic demo scenario and the default scenario is **APT Multi-Stage Campaign**.

### 2. Show the forecast

Open **Forecast timeline**. Explain observed risk as the current telemetry window and projected peak risk as the highest risk predicted across the selected `K` steps.

### 3. Explain the attack stage

Open **MITRE ATT&CK tracker**. The system maps telemetry behavior to reconnaissance, initial access, lateral movement, command and control or exfiltration.

### 4. Show why the model is concerned

Open **XAI feature attribution** and run the analysis. The view shows features contributing to risk, such as SYN behavior, port scanning, timing regularity, high-port traffic or byte volume.

### 5. Show the operational decision

Open **SOC response**. The response combines:

```text
forecast risk x attack-stage severity x asset criticality
```

It returns a P1-P4 priority, response SLA, target asset tier and recommended playbook.

### 6. Close with governance

Open **Audit report** or **History** to show that analyst actions can be reviewed and exported.

## How to Use the Website

### Dashboard controls

| Control | How to use it |
|---|---|
| Data source | Keep **Synthetic Demo Scenario** for the first run, or choose upload mode for a CSV/PCAP file. |
| Scenario | Choose APT, ransomware, DDoS/C2 or benign traffic. |
| Target asset | Select the asset whose business criticality should affect priority. |
| Forecast horizon (`K`) | Increase the horizon to see more future risk steps. |
| Current window | Move through the timeline to inspect attack progression. |
| Alert threshold | Set the level at which projected risk should create an alert. |
| Live stream | Automatically advances through available demonstration windows. |

### Dashboard tabs

1. **Forecast timeline:** compare observed risk with predicted future risk.
2. **MITRE ATT&CK tracker:** view the current and forecasted attack stage.
3. **XAI feature attribution:** run analysis to see the network features driving risk.
4. **K-step simulator:** inspect predicted future feature states.
5. **SOC response:** view priority, asset tier, SLA and recommended playbook.
6. **Model benchmarking:** compare the World Model with the baseline on the supplied windows.
7. **Network topology:** inspect packet records and source/destination context.
8. **Audit report:** review the generated report and exportable decision evidence.

### Uploading your own data

Choose the upload option and provide a supported `.csv` or `.pcap` file. The backend parses the file and creates the same time-window representation used by the synthetic scenarios.

For the most reliable first demonstration, use the built-in synthetic scenario before testing a custom file. Uploaded files must contain traffic fields that the parser can interpret; missing packet-level fields may use parser defaults.

PCAP files normally do not contain attack labels. For those files, the dashboard uses a bounded telemetry-based risk estimate from signals such as SYN/RST ratios, high ports, port scanning and traffic volume. A displayed `0%` means an empty or low-signal time window, not upload progress. Labeled CSV files use their label values when available.

### Investigating an alert

1. Open the alert drawer from the dashboard header.
2. Select **Investigate** to jump to the relevant analysis tab.
3. Review the forecast, MITRE stage, XAI drivers and SOC priority.
4. Acknowledge or simulate isolation when demonstrating the response workflow.
5. Open **History** or **Audit report** to review the recorded action.

## Demonstration Scenarios

| Scenario | Demonstrates |
|---|---|
| APT Multi-Stage Campaign | Benign -> reconnaissance -> access -> lateral movement -> C2 -> exfiltration |
| Ransomware Rapid Outbreak | Faster escalation from access to lateral movement and exfiltration |
| DDoS & C2 Beaconing | Scanning behavior followed by C2 and outbound activity |
| Benign Intranet Baseline | Low-risk comparison behavior |

The synthetic scenarios are repeatable demonstration data. They make the end-to-end workflow easy to evaluate; they are not a replacement for validating the model on independently verified production traffic.

## Architecture

```text
Frontend: Next.js SOC dashboard
    |
    | REST requests
    v
Backend: FastAPI API
    |
    +--> Traffic parser -> 10-second windows -> 25 features
    |
    +--> PyTorch World Model -> K-step future states and risk
    |
    +--> MITRE mapper -> attack stage and technique
    |
    +--> Captum XAI -> top feature drivers and narrative
    |
    +--> SOC prioritizer -> P1-P4, SLA and playbook
    |
    +--> Report and audit outputs
```

## API Overview

The backend routes are mounted under `/api`.

| Method and route | Purpose |
|---|---|
| `GET /healthz` | Confirms that the API and forecaster are ready. |
| `GET /api/scenario` | Generates a selected synthetic scenario. |
| `POST /api/upload` | Parses an uploaded CSV or PCAP file. |
| `POST /api/forecast` | Produces future states and a risk trajectory. |
| `POST /api/mitre` | Maps a state to an ATT&CK stage. |
| `POST /api/xai` | Returns feature attributions and a narrative. |
| `POST /api/soc` | Calculates priority, SLA and playbook. |
| `POST /api/benchmark` | Evaluates supplied predictions and ground truth. |
| `POST /api/report` | Generates an analysis report payload. |

The complete request and response schemas are available through Swagger at http://localhost:8000/docs.

## Local Development Without Docker

### Backend on Windows PowerShell

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd ..
python -m uvicorn backend.main:app --reload --port 8000
```

If PowerShell script execution is restricted, activate the environment from Command Prompt instead:

```bat
backend\.venv\Scripts\activate
```

### Backend from Git Bash

```bash
source backend/.venv/Scripts/activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

Use `uvicorn`, not `unvicorn`.

### Frontend

In a second terminal:

```bash
cd frontend
bun install
bun run dev
```

Open http://localhost:3000. The frontend uses `http://localhost:8000/api` by default. To override it:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api bun run dev
```

On Windows PowerShell:

```powershell
$env:NEXT_PUBLIC_API_URL="http://localhost:8000/api"
bun run dev
```

If Bun is not installed, install it from https://bun.sh/docs/installation, then reopen the terminal. The repository pins Bun through `frontend/package.json`; using the same package manager avoids lockfile differences.

### Environment variables

| Variable | Default | Used by |
|---|---|---|
| `FRONTEND_URL` | `http://localhost:3000,http://127.0.0.1:3000` | Backend CORS configuration |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api` | Frontend API client |
| `ALLOW_SYNTHETIC_FALLBACK` | `true` | Backend model loading fallback for demonstrations |

For a local two-terminal run, start the backend first, confirm http://localhost:8000/healthz, then start the frontend.

## Testing and Validation

### Backend tests

With Docker:

```bash
docker compose exec backend pytest -q
```

With the local virtual environment:

```bash
PYTHONPATH=. python -m pytest backend/tests/ -q
```

From Windows PowerShell, use the equivalent command:

```powershell
$env:PYTHONPATH="."; python -m pytest backend/tests/ -q
```

### Frontend checks

```bash
cd frontend
bun run lint
bun run build
```

## Troubleshooting

### Docker command is not found

Install and start Docker Desktop, then run `docker compose version` before starting the project.

### Port 3000 or 8000 is already in use

Stop the process using the port, or change the published ports in `docker-compose.yml`. If the frontend port changes, update `FRONTEND_URL`, `NEXT_PUBLIC_API_URL` and the URL opened in your browser.

### Dashboard says “Check backend connection”

Check http://localhost:8000/healthz. The backend must be ready before the frontend can request scenarios or forecasts. With Docker, inspect logs using:

```bash
docker compose logs backend
docker compose logs frontend
```

### Backend does not start locally

Make sure the virtual environment is active and run the module form of Uvicorn:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

The command is `uvicorn`, not `unvicorn`.

### Model artifact warning during startup

The development configuration permits a synthetic fallback so the demonstration can still start when a model artifact is unavailable. For production evaluation, verify the model files and disable fallback with:

```bash
ALLOW_SYNTHETIC_FALLBACK=false
```

### Frontend dependency or build issue

From `frontend/`, use the repository's package manager and reinstall dependencies:

```bash
rm -rf node_modules
bun install
bun run build
```

On Windows, remove `node_modules` from File Explorer or use PowerShell `Remove-Item -Recurse -Force node_modules`.

### Upload returns an error or stays empty

- Confirm the file extension is `.csv`, `.pcap` or `.pcapng`.
- Confirm the backend is ready at http://localhost:8000/healthz.
- Check the backend logs with `docker compose logs backend`.
- A capture with no packets or no usable timestamps may produce no time windows.
- PCAP risk is inferred from packet behavior; it is not a ground-truth attack label.

## Project Structure

```text
SIH26/
├── backend/
│   ├── main.py                 FastAPI application and lifecycle
│   ├── routers/                Scenario, upload, forecast, MITRE, XAI, SOC, benchmark, report
│   ├── schemas/                Pydantic request/response contracts
│   ├── src/parser.py           Traffic features and time windows
│   ├── src/world_model.py      LSTM, forecasting, MITRE, SOC and evaluation logic
│   ├── src/explainer.py        Captum GradientShap explanations
│   ├── src/synthetic_generator.py  Repeatable demo scenarios
│   ├── models/                 Model artifacts and benchmark report
│   └── tests/                  Backend tests
├── frontend/src/app/           Dashboard, history and UI components
├── configs/default.yaml        Runtime configuration
├── docker-compose.yml          Local two-service deployment
└── docs/                       Audit, plan and deployment documentation
```

## Important Boundaries

The following points are intentionally explicit for evaluation:

- MITRE mapping is a transparent rule-based layer, not a learned ATT&CK classifier.
- XAI is computed on demand and uses a benign background sequence.
- The default dashboard can use synthetic demonstration data.
- Browser isolation and containment actions record the operator workflow locally; they do not yet call a real EDR, firewall, SIEM or SOAR system.
- Benchmark artifacts and dataset provenance should be independently verified before production accuracy claims.
- Cloud training, model registry, CI/CD and infrastructure-as-code are planned extensions, not current features.

## Documentation

- [Backend audit](README_BACKEND_AUDIT.md)
- [Audit documentation](docs/audit/00_EXECUTIVE_SUMMARY.md)
- [Implementation plan](docs/plan/00_IMPLEMENTATION_PLAN.md)
- [Developer onboarding](docs/audit/11_DEVELOPER_ONBOARDING.md)
- [Production readiness](docs/audit/08_PRODUCTION_READINESS.md)

## Judge Takeaway

**This project moves SOC defense from detecting what happened to forecasting what may happen next, explaining why, prioritizing what matters, and preserving the analyst's decision.**
