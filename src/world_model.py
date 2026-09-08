import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix
from src.parser import FEATURE_COLUMNS

class PyTorchTransitionLSTM(nn.Module):
    """PyTorch LSTM architecture for environment transition dynamics P(S_{t+1} | S_t)."""
    def __init__(self, input_dim: int, hidden_dim: int = 64):
        super(PyTorchTransitionLSTM, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True, num_layers=2)
        # Next state feature vector decoder
        self.state_decoder = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim)
        )
        # Risk score head (Infiltration probability)
        self.risk_head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]
        pred_next_state = self.state_decoder(last_hidden)
        risk_score = self.risk_head(last_hidden)
        return pred_next_state, risk_score

class WorldModelForecaster:
    """
    World Model Dynamic Forecasting Engine.
    Learns P(S_{t+1} | S_t) transition dynamics and performs K-step forward simulation.
    """
    def __init__(self, hidden_dim: int = 64, history_len: int = 4):
        self.feature_cols = FEATURE_COLUMNS
        self.input_dim = len(self.feature_cols)
        self.hidden_dim = hidden_dim
        self.history_len = history_len

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = PyTorchTransitionLSTM(self.input_dim, hidden_dim).to(self.device)

        self.mean_ = np.zeros(self.input_dim)
        self.scale_ = np.ones(self.input_dim)
        self.is_fitted = False

    def fit(self, df_windows: pd.DataFrame, epochs: int = 35, lr: float = 0.005):
        """Fits the World Model on sequential time window state vectors."""
        X_raw = df_windows[self.feature_cols].values.astype(np.float32)

        self.mean_ = np.mean(X_raw, axis=0)
        self.scale_ = np.std(X_raw, axis=0)
        self.scale_[self.scale_ == 0] = 1.0

        X_scaled = (X_raw - self.mean_) / self.scale_

        if 'target_risk_score' in df_windows.columns:
            y_risk = df_windows['target_risk_score'].values.astype(np.float32)
        else:
            y_risk = np.zeros(len(df_windows), dtype=np.float32)

        sequences = []
        target_states = []
        target_risks = []

        for i in range(len(X_scaled) - self.history_len):
            seq = X_scaled[i : i + self.history_len]
            nxt_st = X_scaled[i + self.history_len]
            nxt_rk = y_risk[i + self.history_len]

            sequences.append(seq)
            target_states.append(nxt_st)
            target_risks.append(nxt_rk)

        if len(sequences) == 0:
            self.is_fitted = True
            return

        seq_tensor = torch.tensor(np.array(sequences), dtype=torch.float32).to(self.device)
        st_tensor = torch.tensor(np.array(target_states), dtype=torch.float32).to(self.device)
        rk_tensor = torch.tensor(np.array(target_risks), dtype=torch.float32).unsqueeze(1).to(self.device)

        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        criterion_state = nn.MSELoss()
        criterion_risk = nn.BCELoss()

        self.model.train()
        for ep in range(epochs):
            optimizer.zero_grad()
            pred_st, pred_rk = self.model(seq_tensor)

            loss_st = criterion_state(pred_st, st_tensor)
            loss_rk = criterion_risk(pred_rk, rk_tensor)
            loss = loss_st + 2.0 * loss_rk

            loss.backward()
            optimizer.step()

        self.model.eval()
        self.is_fitted = True

    def save_model(self, filepath: str):
        """Serializes the PyTorch model and scaling parameters."""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted, nothing to save.")
            
        state = {
            'model_state_dict': self.model.state_dict(),
            'mean_': self.mean_,
            'scale_': self.scale_,
            'hidden_dim': self.hidden_dim,
            'history_len': self.history_len
        }
        torch.save(state, filepath)

    @classmethod
    def load_model(cls, filepath: str, device=None) -> 'WorldModelForecaster':
        """Loads a serialized model and scaling parameters."""
        if device is None:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
        state = torch.load(filepath, map_location=device, weights_only=False)
        
        forecaster = cls(hidden_dim=state['hidden_dim'], history_len=state['history_len'])
        forecaster.device = device
        forecaster.model = PyTorchTransitionLSTM(forecaster.input_dim, state['hidden_dim']).to(device)
        forecaster.model.load_state_dict(state['model_state_dict'])
        forecaster.model.eval()
        
        forecaster.mean_ = state['mean_']
        forecaster.scale_ = state['scale_']
        forecaster.is_fitted = True
        
        return forecaster

    def predict_k_steps(
        self,
        historical_windows: pd.DataFrame,
        K: int = 5
    ) -> Dict:
        """
        Performs K-step forward simulation P(S_{t+k} | S_t).
        Projects state vectors and infiltration trajectories K steps into the future.
        """
        if not self.is_fitted:
            raise RuntimeError("WorldModelForecaster must be trained via fit() before predicting.")

        X_raw = historical_windows[self.feature_cols].values.astype(np.float32)
        X_scaled = (X_raw - self.mean_) / self.scale_

        if len(X_scaled) < self.history_len:
            pad_len = self.history_len - len(X_scaled)
            padding = np.tile(X_scaled[0] if len(X_scaled) > 0 else np.zeros(self.input_dim), (pad_len, 1))
            seq_buffer = list(np.vstack([padding, X_scaled]))
        else:
            seq_buffer = list(X_scaled[-self.history_len:])

        self.model.eval()

        forecasted_states_scaled = []
        forecasted_states_unscaled = []
        forecasted_risk_scores = []

        with torch.no_grad():
            for k in range(K):
                current_seq = np.array(seq_buffer[-self.history_len:], dtype=np.float32)
                seq_tensor = torch.tensor(current_seq, dtype=torch.float32).unsqueeze(0).to(self.device)

                pred_st_tensor, pred_rk_tensor = self.model(seq_tensor)

                pred_st = pred_st_tensor.cpu().numpy()[0]
                pred_rk = float(pred_rk_tensor.cpu().numpy()[0, 0])

                seq_buffer.append(pred_st)

                unscaled_st = (pred_st * self.scale_) + self.mean_
                unscaled_st = np.clip(unscaled_st, 0, None)

                forecasted_states_scaled.append(pred_st)
                forecasted_states_unscaled.append(unscaled_st)
                forecasted_risk_scores.append(pred_rk)

        df_forecast = pd.DataFrame(forecasted_states_unscaled, columns=self.feature_cols)
        df_forecast['step_k'] = np.arange(1, K + 1)
        df_forecast['predicted_risk_score'] = forecasted_risk_scores

        return {
            'forecast_df': df_forecast,
            'risk_trajectory': forecasted_risk_scores,
            'forecast_states': forecasted_states_unscaled
        }

class RuleBasedMITREMapper:
    """Rule-Based Post-Processing Module mapping state telemetry vectors to MITRE ATT&CK kill-chain stages using SOC tunable parameters."""

    STAGES = [
        {"name": "Benign", "id": "TA0000", "technique": "Normal Traffic", "color": "#00f5d4", "severity_weight": 1.0},
        {"name": "Reconnaissance", "id": "TA0043", "technique": "T1046 Network Service Scanning", "color": "#00f2fe", "severity_weight": 1.2},
        {"name": "Initial Access", "id": "TA0001", "technique": "T1190 Exploit Public App / T1110 Brute Force", "color": "#ffb703", "severity_weight": 1.5},
        {"name": "Lateral Movement", "id": "TA0008", "technique": "T1021 Remote Services (SMB/RPC/SSH)", "color": "#fb8500", "severity_weight": 1.8},
        {"name": "Command & Control", "id": "TA0011", "technique": "T1071 App Protocol C2 Beaconing", "color": "#ff4d6d", "severity_weight": 2.0},
        {"name": "Exfiltration", "id": "TA0010", "technique": "T1041 Exfiltration Over C2 Channel", "color": "#ff4b4b", "severity_weight": 2.5}
    ]

    SOC_TUNABLE_THRESHOLDS = {
        "exfil_tot_bytes": 50000,
        "exfil_bytes_pkt": 1200,
        "c2_iat_var": 0.005,
        "c2_unique_dsts": 2,
        "c2_tot_bytes": 1000,
        "lateral_unique_dsts": 3,
        "lateral_high_port_ratio": 0.4,
        "initial_syn_ratio": 0.3,
        "initial_bytes_pkt": 300,
        "recon_port_scan_score": 3.0,
        "recon_syn_ratio": 0.5,
        "recon_bytes_pkt": 150
    }

    @classmethod
    def map_state_to_stage(cls, state_dict: Dict, custom_thresholds: Optional[Dict] = None) -> Dict:
        t = custom_thresholds if custom_thresholds is not None else cls.SOC_TUNABLE_THRESHOLDS

        bytes_pkt = state_dict.get('bytes_per_packet_mean', 0)
        tot_bytes = state_dict.get('total_bytes', 0)
        syn_ratio = state_dict.get('syn_flag_ratio', 0)
        unique_ports = state_dict.get('unique_dst_ports', 0)
        port_scan_score = state_dict.get('port_scan_score', 0)
        iat_var = state_dict.get('iat_variance', 0.1)
        unique_dsts = state_dict.get('unique_dst_ips', 1)
        high_port_ratio = state_dict.get('high_port_ratio', 0)

        score_exfil = (tot_bytes > t['exfil_tot_bytes'] or bytes_pkt > t['exfil_bytes_pkt']) * 0.95
        score_c2 = (iat_var < t['c2_iat_var'] and unique_dsts <= t['c2_unique_dsts'] and tot_bytes > t['c2_tot_bytes']) * 0.85
        score_lateral = (unique_dsts >= t['lateral_unique_dsts'] and high_port_ratio > t['lateral_high_port_ratio']) * 0.75
        score_initial = (syn_ratio > t['initial_syn_ratio'] and bytes_pkt > t['initial_bytes_pkt']) * 0.60
        score_recon = (port_scan_score > t['recon_port_scan_score'] or (syn_ratio > t['recon_syn_ratio'] and bytes_pkt < t['recon_bytes_pkt'])) * 0.40

        scores = [0.05, score_recon, score_initial, score_lateral, score_c2, score_exfil]
        max_idx = int(np.argmax(scores))

        stage_info = cls.STAGES[max_idx].copy()
        stage_info['confidence'] = float(max(scores[max_idx], 0.20))
        return stage_info

class AssetCriticalityManager:
    """SOC Asset Inventory & Criticality Management."""

    DEFAULT_ASSETS = {
        "10.0.0.15": {"name": "Domain Controller / Active Directory", "tier": "Tier 1 - Mission Critical", "weight": 2.5, "owner": "SecOps Infra"},
        "10.0.0.5": {"name": "Core SQL Enterprise Database", "tier": "Tier 1 - Mission Critical", "weight": 2.4, "owner": "Data Ops"},
        "198.51.100.44": {"name": "External Perimeter Gateway / DMZ", "tier": "Tier 1 - Mission Critical", "weight": 2.2, "owner": "Network Ops"},
        "10.0.0.50": {"name": "Internal Payroll & HR Server", "tier": "Tier 2 - Business Essential", "weight": 1.7, "owner": "Corporate IT"},
        "192.168.1.100": {"name": "Developer Workstation Endpoint", "tier": "Tier 3 - Standard Endpoint", "weight": 1.2, "owner": "Engineering"}
    }

    @classmethod
    def get_asset_info(cls, ip: str) -> Dict:
        if ip in cls.DEFAULT_ASSETS:
            return cls.DEFAULT_ASSETS[ip]
        # Dynamic subnet resolution
        if ip.startswith("10.0.0."):
            return {"name": f"Internal Infrastructure Host ({ip})", "tier": "Tier 2 - Business Essential", "weight": 1.8, "owner": "IT SecOps"}
        elif ip.startswith("192.168."):
            return {"name": f"Subnet Workstation ({ip})", "tier": "Tier 3 - Standard Endpoint", "weight": 1.2, "owner": "End User"}
        else:
            return {"name": f"External / DMZ Asset ({ip})", "tier": "Tier 1 - Mission Critical", "weight": 2.0, "owner": "Edge Net"}

class SOCRiskPrioritizer:
    """
    Computes SOC Risk Prioritization scores and maps Recommended Response Playbooks.
    """

    @classmethod
    def calculate_prioritized_risk(
        cls,
        forecast_risk: float,
        asset_ip: str,
        mitre_stage: Dict
    ) -> Dict:
        asset_info = AssetCriticalityManager.get_asset_info(asset_ip)
        asset_weight = asset_info['weight']
        stage_weight = mitre_stage.get('severity_weight', 1.0)

        # Composite SOC Priority Score (Normalized 0.0 to 1.0)
        raw_score = forecast_risk * (asset_weight / 2.5) * (stage_weight / 2.5)
        soc_priority_score = min(1.0, max(0.0, raw_score))

        # Priority Level Classification
        if soc_priority_score >= 0.70:
            priority_level = "P1 - CRITICAL"
            color = "#f43f5e"
            badge_bg = "rgba(244, 63, 94, 0.2)"
            sla_response = "Immediate Action (SLA < 15 mins)"
        elif soc_priority_score >= 0.45:
            priority_level = "P2 - HIGH"
            color = "#f59e0b"
            badge_bg = "rgba(245, 158, 11, 0.2)"
            sla_response = "Priority Investigation (SLA < 30 mins)"
        elif soc_priority_score >= 0.25:
            priority_level = "P3 - MEDIUM"
            color = "#38bdf8"
            badge_bg = "rgba(56, 189, 248, 0.2)"
            sla_response = "Standard Queue (SLA < 2 hours)"
        else:
            priority_level = "P4 - LOW"
            color = "#10b981"
            badge_bg = "rgba(16, 185, 129, 0.2)"
            sla_response = "Routine Monitoring (SLA < 24 hours)"

        response_playbook = cls.get_recommended_playbook(mitre_stage['name'], asset_info, priority_level)

        return {
            "soc_priority_score": soc_priority_score,
            "priority_level": priority_level,
            "priority_color": color,
            "badge_bg": badge_bg,
            "sla_response": sla_response,
            "asset_name": asset_info['name'],
            "asset_tier": asset_info['tier'],
            "asset_weight": asset_weight,
            "stage_name": mitre_stage['name'],
            "playbook_actions": response_playbook
        }

    @classmethod
    def get_recommended_playbook(cls, stage_name: str, asset_info: Dict, priority_level: str) -> List[Dict]:
        """Generates dynamic SOC Automated Response Playbooks."""
        asset = asset_info['name']

        if stage_name == "Reconnaissance":
            return [
                {"step": 1, "action": f"Block perimeter scanning source IP on edge firewall for {asset}.", "type": "Automated Network Block", "status": "Ready"},
                {"step": 2, "action": "Enable high-verbosity TCP SYN flood rate-limiting.", "type": "Policy Adjustment", "status": "Ready"},
                {"step": 3, "action": "Trigger automated port scan IOC feed update to SIEM.", "type": "Threat Intel Feed", "status": "Automated"}
            ]
        elif stage_name == "Initial Access":
            return [
                {"step": 1, "action": f"Isolate public-facing service port on target host {asset}.", "type": "Port Isolation", "status": "High Priority"},
                {"step": 2, "action": "Enforce mandatory active session reset and MFA prompt.", "type": "Identity Containment", "status": "Recommended"},
                {"step": 3, "action": "Initiate automated memory capture via EDR sensor for malware payload triage.", "type": "Forensic Capture", "status": "Ready"}
            ]
        elif stage_name == "Lateral Movement":
            return [
                {"step": 1, "action": f"Apply micro-segmentation firewall rule to block SMB (445) and RDP (3389) subnet traversal from {asset}.", "type": "Subnet Containment", "status": "CRITICAL"},
                {"step": 2, "action": "Lock compromised Active Directory service accounts and revoke Kerberos tickets.", "type": "AD Identity Lock", "status": "Urgent"},
                {"step": 3, "action": "Isolate host from local LAN segment while preserving C2 telemetry logging.", "type": "EDR Host Isolation", "status": "Ready"}
            ]
        elif stage_name == "Command & Control":
            return [
                {"step": 1, "action": f"Terminate active C2 socket connection on beaconing port from {asset}.", "type": "Socket Termination", "status": "CRITICAL"},
                {"step": 2, "action": "Sinkhole destination C2 domain and external IP on recursive DNS resolvers.", "type": "DNS Sinkhole", "status": "Urgent"},
                {"step": 3, "action": "Deploy host-based YARA scanning across adjacent subnet endpoints.", "type": "Endpoint Threat Scan", "status": "Automated"}
            ]
        elif stage_name == "Exfiltration":
            return [
                {"step": 1, "action": f"SEVER OUTBOUND WAN INTERFACE for target asset {asset} IMMEDIATELY.", "type": "EMERGENCY CONTAINMENT", "status": "CRITICAL SLA < 5m"},
                {"step": 2, "action": "Trigger automated DLP exfiltration block and dump active TCP socket buffers.", "type": "DLP Block", "status": "Urgent"},
                {"step": 3, "action": "Notify SOC Incident Commander & dispatch Emergency Forensics Response Team.", "type": "Incident Escalation", "status": "Alert Dispatched"}
            ]
        else: # Benign
            return [
                {"step": 1, "action": "Maintain standard telemetry monitoring and logging baseline.", "type": "Routine Monitoring", "status": "Normal"},
                {"step": 2, "action": "No immediate containment action required.", "type": "No Action", "status": "Clear"}
            ]

class BaselineClassifier:
    """Traditional Logistic Regression / Random Forest baseline classifier."""
    def __init__(self):
        self.model = LogisticRegression(max_iter=1000)
        self.feature_cols = FEATURE_COLUMNS
        self.is_fitted = False

    def fit(self, df_windows: pd.DataFrame):
        X = df_windows[self.feature_cols].values
        y = df_windows['is_attack'].values if 'is_attack' in df_windows.columns else (df_windows['target_risk_score'] > 0.30).astype(int)
        self.model.fit(X, y)
        self.is_fitted = True

    def predict_proba(self, df_windows: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            return np.zeros(len(df_windows))
        X = df_windows[self.feature_cols].values
        return self.model.predict_proba(X)[:, 1]

class BenchmarkEvaluator:
    """Evaluates and compares World Model K-step forecaster vs Baseline static classifier."""

    @staticmethod
    def compute_lead_time(wm_probs: np.ndarray, baseline_probs: np.ndarray, threshold: float = 0.50):
        wm_alert_idx = next((i for i, p in enumerate(wm_probs) if p >= threshold), None)
        base_alert_idx = next((i for i, p in enumerate(baseline_probs) if p >= threshold), None)
        if wm_alert_idx is None or base_alert_idx is None:
            return None
        return base_alert_idx - wm_alert_idx

    @staticmethod
    def evaluate_comparison(
        world_model_preds: np.ndarray,
        baseline_preds: np.ndarray,
        ground_truth: np.ndarray,
        threshold: float = 0.50
    ) -> Dict:
        wm_binary = (world_model_preds >= threshold).astype(int)
        base_binary = (baseline_preds >= threshold).astype(int)

        def calc_metrics(preds, gt):
            f1 = float(f1_score(gt, preds, zero_division=0))
            prec = float(precision_score(gt, preds, zero_division=0))
            rec = float(recall_score(gt, preds, zero_division=0))
            tn, fp, fn, tp = confusion_matrix(gt, preds, labels=[0, 1]).ravel()
            fpr = float(fp / max(1, fp + tn))
            return {"f1": f1, "precision": prec, "recall": rec, "fpr": fpr}

        wm_metrics = calc_metrics(wm_binary, ground_truth)
        base_metrics = calc_metrics(base_binary, ground_truth)

        lead_time = BenchmarkEvaluator.compute_lead_time(world_model_preds, baseline_preds, threshold)
        lead_time_wm = lead_time if lead_time is not None else 0.0
        lead_time_base = 0.0

        return {
            "world_model": {**wm_metrics, "lead_time_windows": lead_time_wm},
            "baseline": {**base_metrics, "lead_time_windows": lead_time_base},
            "gain_f1_pct": float((wm_metrics['f1'] - base_metrics['f1']) * 100),
            "lead_time_advantage": lead_time_wm - lead_time_base
        }
