# SIH26153: AI-Based Network Attack Forecasting from Network Traffic Data

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-orange.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red.svg)
![Status](https://img.shields.io/badge/Status-SOC%20Grade%20Operational-brightgreen.svg)
![Theme](https://img.shields.io/badge/UI-Official%20Government%20Portal-darkblue.svg)

Predictive cyber defense system powered by **World Models** that moves beyond static flow classification ("Is this packet malicious?") to predict environment state transition dynamics $P(S_{t+1} | S_t)$ and perform **$K$-step forward simulation** of network attack trajectories before compromise completion.

---

## 🏛️ System Architecture & Paradigm Shift

Traditional Network Intrusion Detection Systems (NIDS) perform static flow classification on isolated packets. In contrast, this **World Model Forecasting Engine**:
1. Aggregates continuous network telemetry into sequential time windows $[T_0, T_1, \dots, T_n]$ forming high-dimensional state vectors $S_t$.
2. Learns transition probability dynamics $P(S_{t+1} | S_t, \dots, S_{t-h})$ using a PyTorch recurrent sequence model.
3. Autoregressively rolls out $K$ steps into the future ($S_{t+1}, S_{t+2}, \dots, S_{t+K}$), computing predicted infiltration trajectories $P(\text{Infiltration} \mid S_{t+k})$.
4. Combines forecast probabilities with **Asset Criticality Tiers** and **MITRE Severity Weights** into an actionable **SOC Risk Prioritization Matrix** with automated response playbooks.
5. Delivers an early warning lead time advantage (**+3.5 time windows ahead**) prior to attack peak completion.

---

## 🌟 Key Features

### 1. 🔮 World Model Dynamic Forecasting Engine
* **Transition Sequence Model**: PyTorch recurrent neural network learning transition dynamics across sequential telemetry windows.
* **$K$-Step Autoregressor**: Projects state vectors and infiltration probabilities $1 \dots 10$ steps into the future.
* **Early Warning Lead Advantage**: Provides pre-compromise alerts before kill-chain completion.

### 2. 🛡️ SOC Risk Prioritization, Asset Criticality & Playbooks
* **Asset Criticality Management**: Categorizes target hosts into Tier 1 (Mission Critical — Domain Controller, Core Database), Tier 2 (Business Essential), and Tier 3 (Standard Endpoints).
* **Composite Risk Prioritization**: Computes Priority Levels (**P1 - CRITICAL**, **P2 - HIGH**, **P3 - MEDIUM**, **P4 - LOW**) with SLA response windows.
* **Automated Playbook Actions**: Generates step-by-step containment actions (firewall block rules, subnet micro-segmentation, DNS sinkholing, host isolation).
* **SOC Action Simulator**: Allows analysts to trigger automated host isolation or micro-segmentation rules directly from the dashboard.

### 3. 📡 Dual-Level Telemetry Parsing Pipeline
* **Dual Input Formats**: Ingests raw `.pcap` / `.pcapng` files (via `scapy` with fallback reader) or structured CSV flow logs (CIC-IDS-2018, CTU-13, UNSW-NB15).
* **Flow & Packet Attributes**: TCP Flags, Flow Duration, Bytes/Packets, IAT stats, TTL stats, TCP Window size, IP fragmentation, payload distributions, port scan signatures.

### 4. 🎯 MITRE ATT&CK Phase Progress Tracker
* Maps telemetry state vectors to 5 core kill-chain stages: Reconnaissance, Initial Access, Lateral Movement, Command & Control (C2), Exfiltration.

### 5. 🔬 Explainable AI (XAI) Engine (SHAP)
* **SHAP Feature Attribution**: Pinpoints top 10 driving telemetry features and generates automated natural language cyber rationale narratives for SOC analysts.

### 6. ⚡ Quantitative Baseline Benchmarking Engine
* Benchmarks World Model $K$-step forecasting against a static Logistic Regression baseline classifier across **$F1$-Score, Precision, Recall, FPR, and Detection Lead Time**.

### 7. 🏛️ Official Government Portal Web UI
* Clean light-mode interface (`#f8fafc` background, `#0f172a` header banner, equal-height metric cards).
* **8 Interactive Views**: Forecast Timeline, MITRE Tracker, XAI Feature Attribution, $K$-Step State Simulator, SOC Response & Risk Prioritization, Model Benchmarking, Network Topology Inspector, and Audit Report Exporter.

---

## 📁 Repository Structure

```
SIH26153/
├── app.py                      # Standalone Streamlit Web Dashboard
├── README.md                   # System Documentation
├── Features.md                 # Technical Specifications & Feature Matrix
├── render.yaml                 # Render Infrastructure-as-Code Manifest
├── Dockerfile                  # Container Build Configuration
├── Procfile                    # Web Process Start Command
├── requirements.txt            # Python Dependencies
├── src/
│   ├── __init__.py             # Package Initializer
│   ├── parser.py               # PCAP & CSV Telemetry Feature Extractor
│   ├── synthetic_generator.py  # Multi-Stage Cyber Attack Dataset Generator
│   ├── world_model.py          # World Model, Asset Criticality & SOC Prioritizer
│   └── explainer.py            # SHAP Feature Attribution & XAI Engine
└── tests/
    └── test_pipeline.py        # Automated Pytest Test Suite
```

---

## 🚀 Production Deployment Guide

### 💡 Vercel vs Render Evaluation
* **Vercel**: Vercel is optimized for static sites, Next.js, and serverless short-lived functions. Streamlit requires a persistent, long-running Python process with active WebSocket connections, which is **not supported on Vercel's serverless architecture**.
* **Render (RECOMMENDED)**: **Render** provides native support for long-running Python Web Services with persistent WebSocket support, automated GitHub continuous deployment on `git push`, and free-tier compatibility!

---

### 🌐 Deploying to Render (2-Minute Setup)

1. Sign in to [Render.com](https://render.com) using your GitHub account (`Asachdeva001`).
2. Click **New +** $\to$ **Web Service**.
3. Connect your private repository: `Asachdeva001/SIH26153`.
4. Render will automatically detect `render.yaml` or you can set:
   * **Name**: `sih26153-attack-forecasting`
   * **Environment**: `Python 3`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
5. Click **Create Web Service**. Your application will be live in 2 minutes!

---

### ☁️ Alternative Option: Streamlit Community Cloud (100% Free)
1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Click **New App** $\to$ Select repo `Asachdeva001/SIH26153`, branch `main`, main file `app.py`.
3. Click **Deploy!**

---

## 🛠️ Local Installation & Development

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch Local Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 3. Run Automated Unit Test Suite
```bash
python -m pytest tests/test_pipeline.py -v
```

---

## 📄 Exporting Security Audit Reports
From the **Audit Report** tab, SOC incident responders can export comprehensive threat intelligence reports in JSON format.
