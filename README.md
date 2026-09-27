# Network State World Model & Attack Forecaster (SIH)

This project provides an AI-powered software prototype that learns the evolving state of a computer network from traffic telemetry and predicts the likelihood and progression of malicious activity *before* a compromise is completed. 

By leveraging the emerging concept of **World Models**, this system ingests network traffic, learns temporal behaviors, forecasts future attack states, and provides interpretable decision support for SOC defenders.

## 🚀 Key Features

*   **Traffic Parser & Windowing:** Ingests raw PCAP/CSV network telemetry and creates temporal state windows.
*   **World Model Forecaster (PyTorch):** Learns environment transition dynamics ($P(S_{t+1} | S_t)$) using an LSTM-based sequence model to forecast future states $K$-steps ahead.
*   **Attack Explainer (XAI):** Uses SHAP (GradientShap) to provide local interpretability, attributing predicted risk to specific network features and mapping them to MITRE ATT&CK tactics.
*   **SOC Prioritization:** Integrates asset criticality scores with forecast risk to output actionable alerts.
*   **Robust Backend:** FastAPI-based backend with async processing, robust error handling, and comprehensive logging.

## 🏗️ Architecture

The solution is containerized using Docker and divided into two main services:

1.  **Backend (FastAPI & PyTorch):** Handles data parsing, model inference, XAI computation, and metric evaluation.
2.  **Frontend (Next.js & React):** Provides a dashboard for SOC analysts to upload data, view forecasts, and analyze XAI narratives.

## 🛠️ Prerequisites

*   Docker Desktop (or Docker Engine + Docker Compose)
*   At least 8GB RAM (16GB recommended for model training)

## ⚙️ Setup & Installation

The entire stack is containerized for easy, reproducible deployment.

1.  **Clone the repository:**
    ```bash
    git clone <repo-url>
    cd SIH26
    ```

2.  **Build and Start the Services:**
    ```bash
    docker-compose up -d --build
    ```

3.  **Access the Dashboard:**
    *   Frontend UI: [http://localhost:3000](http://localhost:3000)
    *   Backend API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

## 📡 API Endpoints (Backend)

*   `GET /healthz`: Deep health check (checks API, ML models, and XAI explainer status).
*   `POST /upload`: Uploads and parses CSV/PCAP network telemetry into time windows.
*   `GET /scenario`: Generates synthetic multi-stage attack scenarios for testing.
*   `POST /forecast`: Uses the World Model to predict network states $K$-steps into the future.
*   `POST /xai`: Explains model predictions using SHAP and maps features to MITRE tactics.
*   `POST /soc/prioritize`: Calculates final SOC alert priorities based on forecasted risk and asset criticality.
*   `POST /benchmark`: Evaluates the World Model against a Baseline classifier using chronological split data.

## 🧪 Testing

The backend is fully unit-tested with `pytest`. To run the test suite inside the container:

```bash
docker-compose exec backend pytest -v
```

Or locally (if Python environment is set up):

```bash
python -m pytest backend/tests/ -v
```

## 📁 Project Structure

```text
SIH26/
├── backend/
│   ├── models/            # Serialized ML artifacts & loader logic
│   ├── routers/           # FastAPI endpoints
│   ├── schemas/           # Pydantic validation models
│   ├── scripts/           # Training & dataset download scripts
│   ├── src/               # Core ML logic (Parser, WorldModel, Explainer)
│   ├── tests/             # Pytest suite
│   ├── main.py            # FastAPI application entrypoint
│   └── requirements.txt   # Python dependencies
├── configs/
│   └── default.yaml       # Global configuration parameters
├── frontend/
│   ├── src/               # React components and pages
│   ├── Dockerfile         # Frontend build instructions
│   └── package.json       # Node dependencies
└── docker-compose.yml     # Orchestration configuration
```
