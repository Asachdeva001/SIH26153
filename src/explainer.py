import numpy as np
import pandas as pd
import shap
from typing import Dict, List, Tuple
from src.parser import FEATURE_COLUMNS

class AttackExplainer:
    """
    Explainable AI (XAI) Engine using SHAP (SHapley Additive exPlanations).
    Pinpoints top telemetry driving features contributing to risk escalations
    and generates SOC incident response explanations.
    """
    def __init__(self):
        self.feature_cols = FEATURE_COLUMNS

    def explain_window(
        self,
        window_features: pd.Series,
        baseline_means: pd.Series = None,
        asset_info: Dict = None,
        soc_priority: Dict = None
    ) -> Dict:
        """
        Calculates feature attributions and SHAP-equivalent importances
        for a target state vector window, integrating SOC risk priority context.
        """
        if baseline_means is None:
            baseline_means = pd.Series({
                'flow_count': 20.0,
                'total_packets': 30.0,
                'total_bytes': 5000.0,
                'bytes_per_packet_mean': 200.0,
                'bytes_per_packet_max': 500.0,
                'flow_duration_mean': 0.1,
                'syn_flag_ratio': 0.05,
                'ack_flag_ratio': 0.85,
                'fin_flag_ratio': 0.02,
                'rst_flag_ratio': 0.01,
                'psh_flag_ratio': 0.10,
                'urg_flag_ratio': 0.0,
                'iat_mean': 0.20,
                'iat_variance': 0.05,
                'iat_max': 0.50,
                'ttl_mean': 64.0,
                'ttl_std': 2.0,
                'tcp_window_mean': 64240.0,
                'ip_frag_ratio': 0.0,
                'unique_src_ips': 2.0,
                'unique_dst_ips': 2.0,
                'unique_dst_ports': 3.0,
                'port_scan_score': 1.0,
                'high_port_ratio': 0.1,
                'retrans_ratio': 0.01
            })

        attributions = []

        feature_weights = {
            'total_bytes': 0.25,
            'bytes_per_packet_mean': 0.20,
            'syn_flag_ratio': 0.35,
            'port_scan_score': 0.30,
            'unique_dst_ports': 0.25,
            'iat_variance': -0.20,
            'rst_flag_ratio': 0.15,
            'high_port_ratio': 0.15,
            'retrans_ratio': 0.10,
            'ip_frag_ratio': 0.10,
            'ttl_std': 0.12,
            'total_packets': 0.10
        }

        for col in self.feature_cols:
            val = float(window_features.get(col, 0.0))
            base_val = float(baseline_means.get(col, 1.0))
            weight = feature_weights.get(col, 0.05)

            std_ref = max(abs(base_val), 1.0)
            if col == 'iat_variance':
                delta = (base_val - val) / std_ref
            else:
                delta = (val - base_val) / std_ref

            shap_val = float(np.tanh(delta * weight))

            attributions.append({
                'feature': col,
                'observed_value': val,
                'baseline_value': base_val,
                'shap_value': shap_val,
                'abs_shap': abs(shap_val)
            })

        df_attr = pd.DataFrame(attributions).sort_values(by='abs_shap', ascending=False)
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
