# Project Features & Technical Specifications

---

## 1. 🔮 World Model & Predictive Forecasting Engine

* **Transition Dynamics Model $P(S_{t+1} | S_t)$**: Uses a PyTorch recurrent sequence neural network to model environment transition dynamics rather than static flow classification.
* **$K$-Step Autoregressive Forward Simulator**: Projects network behavior $1 \dots 10$ time windows into the future, outputting time-series infiltration probability trajectories before compromise completion.
* **Early Warning Lead Advantage**: Provides an estimated **+3.5 window lead time advantage** over static classifiers, giving SOC teams pre-compromise early warnings.

---

## 2. 🛡️ SOC Risk Prioritization, Asset Criticality & Playbooks (NEW)

* **Asset Inventory & Criticality Management**:
  * **Tier 1 - Mission Critical** (Weight: $2.5\times$ — Domain Controller `10.0.0.15`, Core SQL Database `10.0.0.5`, Edge Gateway `198.51.100.44`).
  * **Tier 2 - Business Essential** (Weight: $1.7\times - 1.8\times$ — HR / Payroll Servers).
  * **Tier 3 - Standard Endpoints** (Weight: $1.2\times$ — Subnet Workstations).
* **Composite SOC Risk Prioritization**:
  * Calculates Composite Risk Score: $\text{Forecast Risk} \times \text{Asset Weight} \times \text{MITRE Severity}$.
  * Priority Levels: **P1 - CRITICAL** ($\ge 70\%$, SLA $<15$ mins), **P2 - HIGH**, **P3 - MEDIUM**, **P4 - LOW**.
* **Recommended Automated Response Playbooks**:
  * **Reconnaissance**: Perimeter IP blocking, SYN flood rate-limiting.
  * **Initial Access**: Port isolation, MFA reset prompt, EDR memory capture.
  * **Lateral Movement**: Subnet SMB/RDP micro-segmentation, Active Directory service account lock.
  * **Command & Control (C2)**: Outbound socket termination, DNS C2 sinkholing.
  * **Exfiltration**: Emergency WAN interface isolation, DLP payload block.
* **Interactive SOC Response Simulator**: Trigger automated EDR host isolation, micro-segmentation firewall rules, or analyst ticket assignment directly from the portal UI.

---

## 3. 📡 Dual-Level Telemetry Feature Pipeline

* **Multi-Format Data Ingestion**: Parses raw `.pcap` / `.pcapng` packet captures (via `scapy` with fallback reader) and structured CSV flow logs (`CIC-IDS-2018`, `CTU-13`, `UNSW-NB15`).
* **Flow-Level Attributes**:
  * Src/Dst IP, Src/Dst Port, Protocol
  * TCP Bitmask Flags (`SYN`, `ACK`, `FIN`, `RST`, `PSH`, `URG`)
  * Flow Duration, Bytes/Packets per flow
  * Inter-Arrival Time (IAT) statistics (mean, variance, max)
* **Packet-Level Attributes**:
  * Time-To-Live (TTL) statistics (mean, std)
  * TCP Window Size, IP Fragmentation flags
  * Payload size distributions, Port scan signatures, packet retransmissions
* **Sequential Windowing**: Aggregates continuous traffic into sequential time windows $[T_0, T_1, \dots, T_n]$ forming high-dimensional state vectors $S_t$.

---

## 4. 🎯 MITRE ATT&CK Phase Progress Tracker

* **5-Stage Kill-Chain Mapping**: Maps telemetry state vectors to official MITRE ATT&CK stages:
  1. **Reconnaissance** (*T1046 Network Service Scanning / T1595 Active Scanning*)
  2. **Initial Access** (*T1190 Exploit Public-Facing App / T1110 Brute Force*)
  3. **Lateral Movement** (*T1021 Remote Services / SMB / RPC / SSH*)
  4. **Command & Control (C2)** (*T1071 App Protocol Beaconing*)
  5. **Exfiltration** (*T1041 Exfiltration Over C2 Channel*)
* **Confidence & Technique Details**: Displays phase status (`ACTIVE`, `FORECASTED`, `COMPLETED`), confidence scores, and technique IDs.

---

## 5. 🔬 Explainable AI (XAI) Engine (SHAP)

* **Feature Attribution Analysis**: Uses SHAP (SHapley Additive exPlanations) to identify top 10 driving telemetry features (e.g., TCP SYN flag spikes, anomalous payload sizes, low IAT variance beaconing, port scan scores).
* **Interactive Impact Charts**: Visualizes metric contribution values for any selected time window $T_{now}$ or projected step $T_{now+K}$.
* **Automated Cyber Rationale**: Generates natural language narratives translating raw telemetry spikes into actionable explanations for SOC incident responders.

---

## 6. ⚡ Quantitative Baseline Benchmarking Engine

* **Baseline Classifier**: Trains a traditional static Logistic Regression model on the same telemetry windows.
* **Metrics Evaluated**: Compares $F1$-score, Precision, Recall, False Positive Rate (FPR), and Detection Lead Time.
* **Comparative Visualizations**: Provides side-by-side metric tables and Plotly comparison bar charts demonstrating World Model superiority.

---

## 7. 🛡️ Built-in Multi-Stage Cyber Attack Generator

* **Offline Demo Scenarios**: Pre-configured realistic datasets for instant offline evaluation without external files:
  * **APT Multi-Stage Campaign** (Full Recon $\to$ Initial Access $\to$ Lateral Movement $\to$ C2 $\to$ Exfiltration)
  * **Ransomware Rapid Outbreak**
  * **DDoS & C2 Beaconing**
  * **Benign Intranet Baseline**

---

## 8. 🏛️ Official Government Portal Web UI

* **Clean Light-Mode Aesthetic**: High-contrast white background canvas (`#f8fafc`), deep navy official header banner (`#0f172a`), and perfectly aligned equal-height metric cards (`145px`).
* **8 Interactive Views**:
  1. 📈 **Forecast Timeline**: Interactive Plotly graph of observed telemetry risk vs $K$-step forecast with threshold alert bands.
  2. 🎯 **MITRE ATT&CK Tracker**: Visual 5-stage progress pipeline.
  3. 🔬 **XAI Feature Attribution**: SHAP impact waterfall/bar charts and cyber rationale.
  4. 🔮 **$K$-Step State Simulator**: Projected state vector tables and feature drift timelines.
  5. 🛡️ **SOC Response & Risk Prioritization**: Asset criticality tiers, P1-P4 priority score, SLA window & automated response playbooks.
  6. ⚡ **Model Benchmarking**: Quantitative World Model vs Baseline comparison matrix.
  7. 🌐 **Network Topology & Flow Inspector**: Host communication breakdown and raw packet log table.
  8. 📄 **Audit Report Exporter**: One-click download for executive JSON threat forecast reports.