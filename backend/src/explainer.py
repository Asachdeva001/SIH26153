import torch
import torch.nn as nn
from captum.attr import GradientShap
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from backend.src.parser import FEATURE_COLUMNS

class RiskScoreWrapper(nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model
    def forward(self, x):
        _, risk_score = self.model(x)
        return risk_score

class AttackExplainer:
    """
    Explainable AI (XAI) Engine using Captum GradientShap on actual PyTorch models.
    Pinpoints top telemetry driving features contributing to risk escalations
    and generates SOC incident response explanations.
    """
    def __init__(self, model, history_len, mean, scale, device, background_df):
        self.feature_cols = FEATURE_COLUMNS
        self.history_len = history_len
        self.mean_ = mean
        self.scale_ = scale
        self.device = device

        self.wrapper_model = RiskScoreWrapper(model).to(device)
        self.wrapper_model.eval()
        self.gs = GradientShap(self.wrapper_model)
        
        # Prepare background dataset (up to 200 sequences)
        self.background_tensor = self._prepare_sequences(background_df, max_samples=200)

    def _prepare_sequences(self, df, max_samples=None):
        X_raw = df[self.feature_cols].values.astype(np.float32)
        X_scaled = (X_raw - self.mean_) / self.scale_
        
        sequences = []
        for i in range(len(X_scaled) - self.history_len + 1):
            sequences.append(X_scaled[i : i + self.history_len])
            
        if len(sequences) == 0:
            pad = np.zeros((self.history_len, len(self.feature_cols)), dtype=np.float32)
            sequences.append(pad)
            
        seq_array = np.array(sequences)
        if max_samples and len(seq_array) > max_samples:
            idx = np.random.choice(len(seq_array), max_samples, replace=False)
            seq_array = seq_array[idx]
            
        return torch.tensor(seq_array, dtype=torch.float32).to(self.device)

    def explain_window(
        self,
        historical_windows: pd.DataFrame,
        asset_info: Dict = None,
        soc_priority: Dict = None
    ) -> Dict:
        """
        Calculates feature attributions and SHAP-equivalent importances
        for a target state vector window, integrating SOC risk priority context.
        """
        X_raw = historical_windows[self.feature_cols].values.astype(np.float32)
        X_scaled = (X_raw - self.mean_) / self.scale_
        
        if len(X_scaled) < self.history_len:
            pad_len = self.history_len - len(X_scaled)
            padding = np.tile(X_scaled[0] if len(X_scaled) > 0 else np.zeros(len(self.feature_cols)), (pad_len, 1))
            seq = np.vstack([padding, X_scaled])
        else:
            seq = X_scaled[-self.history_len:]
            
        input_tensor = torch.tensor(seq, dtype=torch.float32, requires_grad=True).unsqueeze(0).to(self.device)
        
        attributions = self.gs.attribute(input_tensor, baselines=self.background_tensor, target=0, n_samples=50)
        
        # attributions shape: (1, history_len, num_features)
        attr_matrix = attributions[0].cpu().detach().numpy() # (history_len, num_features)
        
        abs_importance = np.abs(attr_matrix).sum(axis=0)
        net_contribution = attr_matrix.sum(axis=0)
        
        attr_list = []
        current_row = historical_windows.iloc[-1]
        for idx, col in enumerate(self.feature_cols):
            val = float(current_row.get(col, 0.0))
            base_val = float(self.mean_[idx]) if self.mean_ is not None else 1.0
            
            attr_list.append({
                'feature': col,
                'observed_value': val,
                'baseline_value': base_val,
                'shap_value': float(net_contribution[idx]),
                'abs_shap': float(abs_importance[idx]),
                'per_timestep': attr_matrix[:, idx].tolist()
            })
            
        df_attr = pd.DataFrame(attr_list).sort_values(by='abs_shap', ascending=False)
        top_10 = df_attr.head(10).to_dict(orient='records')
        
        top_driver = top_10[0]
        narrative = self._generate_narrative(top_driver, asset_info, soc_priority)
        
        return {
            'attributions': top_10,
            'full_attributions_df': df_attr,
            'primary_driver': top_driver['feature'],
            'narrative': narrative
        }

    def _generate_narrative(
        self,
        driver: Dict,
        asset_info: Dict = None,
        soc_priority: Dict = None
    ) -> str:
        feat = driver['feature']
        obs = driver['observed_value']
        base = driver['baseline_value']

        asset_str = f" Target Asset: {asset_info['name']} ({asset_info['tier']})." if asset_info else ""
        prio_str = f" Priority Level: {soc_priority['priority_level']}." if soc_priority else ""

        if feat == 'syn_flag_ratio':
            core = f"TCP SYN flag spike observed ({obs*100:.1f}% vs normal {base*100:.1f}%). Active SYN flood / service scanning targeting internal infrastructure."
        elif feat == 'total_bytes' or feat == 'bytes_per_packet_mean':
            core = f"Anomalous byte volume detected ({obs:.0f} bytes/pkt vs baseline {base:.0f} bytes/pkt). High risk of exfiltration payload delivery."
        elif feat == 'port_scan_score' or feat == 'unique_dst_ports':
            core = f"Port scan signature identified (Score: {obs:.1f}, Unique Ports: {obs:.0f}). Host actively probing network perimeter."
        elif feat == 'iat_variance':
            core = f"Highly regular Inter-Arrival Time detected (Variance: {obs:.5f}). Strong signature of Command & Control (C2) heartbeat beaconing."
        elif feat == 'high_port_ratio':
            core = f"Elevated high-port traffic ratio ({obs*100:.1f}%). Potential SMB/RPC lateral movement or unassigned C2 channel."
        else:
            core = f"Telemetry metric '{feat}' drifted to {obs:.2f} (baseline: {base:.2f}), elevating multi-step forecast risk."

        return f"{core}{asset_str}{prio_str}"

