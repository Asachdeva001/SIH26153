import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
from src.parser import FEATURE_COLUMNS, TrafficParser

class SyntheticAttackGenerator:
    """
    Generates realistic multi-stage cyber attack telemetry datasets
    for offline evaluation, demonstration, and baseline benchmarking.
    """

    SCENARIOS = [
        "APT Multi-Stage Campaign",
        "Ransomware Rapid Outbreak",
        "DDoS & C2 Beaconing",
        "Benign Intranet Baseline"
    ]

    def __init__(self, seed: int = 42):
        np.random.seed(seed)

    def generate_scenario(
        self,
        scenario_name: str = "APT Multi-Stage Campaign",
        num_windows: int = 20,
        window_size_sec: float = 10.0
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generates both raw packet-level flow DataFrame and aggregated windowed state DataFrame.
        """
        if scenario_name == "Benign Intranet Baseline":
            return self._generate_benign(num_windows, window_size_sec)
        elif scenario_name == "Ransomware Rapid Outbreak":
            return self._generate_ransomware(num_windows, window_size_sec)
        elif scenario_name == "DDoS & C2 Beaconing":
            return self._generate_ddos_c2(num_windows, window_size_sec)
        else:
            # Default: APT Multi-Stage Campaign
            return self._generate_apt_multistage(num_windows, window_size_sec)

    def _generate_apt_multistage(
        self,
        num_windows: int = 20,
        window_size_sec: float = 10.0
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Constructs an explicit 5-stage MITRE ATT&CK progression across time windows:
        - Windows 0-3: Benign Baseline
        - Windows 4-6: Reconnaissance (Port Scan, IP Sweep)
        - Windows 7-9: Initial Access (Brute Force / Exploit Payload)
        - Windows 10-12: Lateral Movement (Subnet Host Fan-out, SMB/RPC)
        - Windows 13-15: Command & Control (C2 Periodic Beaconing)
        - Windows 16-19: Data Exfiltration (Massive Outbound Bytes)
        """
        raw_rows = []

        for w in range(num_windows):
            start_t = w * window_size_sec

            # Determine phase for window
            if w <= 3:
                stage = "Benign"
                n_pkts = np.random.randint(15, 30)
            elif 4 <= w <= 6:
                stage = "Reconnaissance"
                n_pkts = np.random.randint(60, 120)
            elif 7 <= w <= 9:
                stage = "Initial Access"
                n_pkts = np.random.randint(80, 150)
            elif 10 <= w <= 12:
                stage = "Lateral Movement"
                n_pkts = np.random.randint(70, 130)
            elif 13 <= w <= 15:
                stage = "Command & Control"
                n_pkts = np.random.randint(40, 70)
            else:
                stage = "Exfiltration"
                n_pkts = np.random.randint(120, 250)

            for i in range(n_pkts):
                t = start_t + (i / max(1, n_pkts)) * (window_size_sec - 0.1)

                if stage == "Benign":
                    src_ip = f"192.168.1.{np.random.randint(10, 25)}"
                    dst_ip = "10.0.0.5"
                    src_port = np.random.randint(49152, 65000)
                    dst_port = np.random.choice([80, 443, 53])
                    syn = 1 if i % 10 == 0 else 0
                    ack = 1
                    rst = 0
                    bytes_pkt = np.random.randint(100, 800)
                    ttl = 64
                    payload = np.random.randint(50, 400)
                    retrans = 0
                    iat_m = np.random.uniform(0.1, 0.4)

                elif stage == "Reconnaissance":
                    src_ip = "192.168.1.100"  # Attacker scanner IP
                    dst_ip = f"10.0.0.{np.random.randint(1, 50)}"
                    src_port = np.random.randint(30000, 60000)
                    dst_port = np.random.randint(1, 1024)  # Port scan signature
                    syn = 1  # SYN probe flood
                    ack = 0
                    rst = 1 if np.random.rand() > 0.4 else 0
                    bytes_pkt = 64
                    ttl = np.random.choice([64, 128, 255])
                    payload = 0
                    retrans = 0
                    iat_m = 0.005  # High frequency

                elif stage == "Initial Access":
                    src_ip = "192.168.1.100"
                    dst_ip = "10.0.0.15"  # Targeted web server
                    src_port = np.random.randint(40000, 50000)
                    dst_port = np.random.choice([80, 443, 8080, 445])
                    syn = 1 if i % 3 == 0 else 0
                    ack = 1
                    rst = 1 if i % 4 == 0 else 0
                    bytes_pkt = np.random.randint(400, 1500)
                    ttl = 64
                    payload = np.random.randint(300, 1200)
                    retrans = 1 if np.random.rand() > 0.7 else 0
                    iat_m = 0.02

                elif stage == "Lateral Movement":
                    src_ip = f"10.0.0.{np.random.randint(10, 16)}"  # Compromised host pivoting
                    dst_ip = f"10.0.0.{np.random.randint(20, 45)}"  # Internal host sweep
                    src_port = np.random.randint(45000, 60000)
                    dst_port = np.random.choice([445, 135, 3389, 22])  # SMB/RDP/SSH
                    syn = 1 if i % 2 == 0 else 0
                    ack = 1
                    rst = 0
                    bytes_pkt = np.random.randint(200, 1000)
                    ttl = 128
                    payload = np.random.randint(150, 800)
                    retrans = 0
                    iat_m = 0.05

                elif stage == "Command & Control":
                    src_ip = "10.0.0.15"
                    dst_ip = "198.51.100.44"  # External C2 Server
                    src_port = 49200
                    dst_port = 8443  # C2 port
                    syn = 0
                    ack = 1
                    rst = 0
                    bytes_pkt = np.random.choice([128, 256])  # Heartbeat signature
                    ttl = 54
                    payload = 128
                    retrans = 0
                    iat_m = 1.0  # Periodic heartbeat beaconing

                else:  # Exfiltration
                    src_ip = "10.0.0.15"
                    dst_ip = "198.51.100.44"
                    src_port = 49201
                    dst_port = 443
                    syn = 0
                    ack = 1
                    rst = 0
                    bytes_pkt = np.random.randint(1400, 4000)  # Massive jumbo packets
                    ttl = 54
                    payload = np.random.randint(1200, 3800)
                    retrans = 1 if np.random.rand() > 0.8 else 0
                    iat_m = 0.001  # Maximum burst throughput

                raw_rows.append({
                    'timestamp': pd.Timestamp('2026-08-30 10:00:00') + pd.Timedelta(seconds=t),
                    'relative_sec': t,
                    'src_ip': src_ip,
                    'dst_ip': dst_ip,
                    'src_port': src_port,
                    'dst_port': dst_port,
                    'protocol': 6,
                    'syn_flag': syn,
                    'ack_flag': ack,
                    'fin_flag': 0,
                    'rst_flag': rst,
                    'psh_flag': 1 if bytes_pkt > 500 else 0,
                    'urg_flag': 0,
                    'flow_duration': 0.05,
                    'tot_bytes': bytes_pkt,
                    'tot_pkts': 1,
                    'flow_iat_mean': iat_m,
                    'flow_iat_std': iat_m * 0.1,
                    'flow_iat_max': iat_m * 2.0,
                    'ttl': ttl,
                    'tcp_win': 64240,
                    'ip_frag': 0,
                    'payload_bytes': payload,
                    'retrans_count': retrans,
                    'ground_truth_stage': stage
                })

        df_raw = pd.DataFrame(raw_rows)
        parser = TrafficParser(window_size_sec=window_size_sec)
        df_windows = parser.create_time_windows(df_raw)

        # Attach ground truth phase & risk scores to windows
        stage_map = {
            "Benign": 0.05,
            "Reconnaissance": 0.25,
            "Initial Access": 0.50,
            "Lateral Movement": 0.70,
            "Command & Control": 0.85,
            "Exfiltration": 0.98
        }

        ground_truths = []
        risk_labels = []

        for w_idx in range(len(df_windows)):
            if w_idx <= 3:
                st = "Benign"
            elif 4 <= w_idx <= 6:
                st = "Reconnaissance"
            elif 7 <= w_idx <= 9:
                st = "Initial Access"
            elif 10 <= w_idx <= 12:
                st = "Lateral Movement"
            elif 13 <= w_idx <= 15:
                st = "Command & Control"
            else:
                st = "Exfiltration"
            ground_truths.append(st)
            risk_labels.append(stage_map[st])

        df_windows['ground_truth_stage'] = ground_truths
        df_windows['target_risk_score'] = risk_labels
        df_windows['is_attack'] = (df_windows['target_risk_score'] > 0.30).astype(int)

        return df_raw, df_windows

    def _generate_benign(self, num_windows: int, window_size_sec: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generates benign network baseline without malicious escalations."""
        raw_rows = []
        for w in range(num_windows):
            start_t = w * window_size_sec
            n_pkts = np.random.randint(20, 45)
            for i in range(n_pkts):
                t = start_t + (i / max(1, n_pkts)) * (window_size_sec - 0.1)
                raw_rows.append({
                    'timestamp': pd.Timestamp('2026-08-30 10:00:00') + pd.Timedelta(seconds=t),
                    'relative_sec': t,
                    'src_ip': f"192.168.1.{np.random.randint(10, 50)}",
                    'dst_ip': f"10.0.0.{np.random.randint(1, 10)}",
                    'src_port': np.random.randint(49152, 65000),
                    'dst_port': np.random.choice([80, 443, 53, 8080]),
                    'protocol': 6,
                    'syn_flag': 1 if i % 8 == 0 else 0,
                    'ack_flag': 1,
                    'fin_flag': 0,
                    'rst_flag': 0,
                    'psh_flag': 1 if i % 4 == 0 else 0,
                    'urg_flag': 0,
                    'flow_duration': 0.08,
                    'tot_bytes': np.random.randint(200, 900),
                    'tot_pkts': 1,
                    'flow_iat_mean': np.random.uniform(0.1, 0.5),
                    'flow_iat_std': 0.05,
                    'flow_iat_max': 0.8,
                    'ttl': 64,
                    'tcp_win': 64240,
                    'ip_frag': 0,
                    'payload_bytes': np.random.randint(100, 500),
                    'retrans_count': 0,
                    'ground_truth_stage': 'Benign'
                })

        df_raw = pd.DataFrame(raw_rows)
        parser = TrafficParser(window_size_sec=window_size_sec)
        df_windows = parser.create_time_windows(df_raw)
        df_windows['ground_truth_stage'] = 'Benign'
        df_windows['target_risk_score'] = 0.05
        df_windows['is_attack'] = 0
        return df_raw, df_windows

    def _generate_ransomware(self, num_windows: int, window_size_sec: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generates fast ransomware outbreak (Initial Access -> Lateral Movement -> Exfil)."""
        df_raw, df_win = self._generate_apt_multistage(num_windows, window_size_sec)
        # Shift escalation timeline faster
        ground_truths = []
        risk_labels = []
        for w_idx in range(len(df_win)):
            if w_idx <= 1:
                st = "Benign"
            elif 2 <= w_idx <= 4:
                st = "Initial Access"
            elif 5 <= w_idx <= 9:
                st = "Lateral Movement"
            else:
                st = "Exfiltration"
            ground_truths.append(st)
            stage_map = {"Benign": 0.05, "Initial Access": 0.55, "Lateral Movement": 0.80, "Exfiltration": 0.96}
            risk_labels.append(stage_map[st])

        df_win['ground_truth_stage'] = ground_truths
        df_win['target_risk_score'] = risk_labels
        df_win['is_attack'] = (df_win['target_risk_score'] > 0.30).astype(int)
        return df_raw, df_win

    def _generate_ddos_c2(self, num_windows: int, window_size_sec: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generates DDoS SYN Probing leading to Command & Control channel."""
        df_raw, df_win = self._generate_apt_multistage(num_windows, window_size_sec)
        ground_truths = []
        risk_labels = []
        for w_idx in range(len(df_win)):
            if w_idx <= 2:
                st = "Benign"
            elif 3 <= w_idx <= 8:
                st = "Reconnaissance"
            elif 9 <= w_idx <= 14:
                st = "Command & Control"
            else:
                st = "Exfiltration"
            ground_truths.append(st)
            stage_map = {"Benign": 0.05, "Reconnaissance": 0.35, "Command & Control": 0.75, "Exfiltration": 0.95}
            risk_labels.append(stage_map[st])

        df_win['ground_truth_stage'] = ground_truths
        df_win['target_risk_score'] = risk_labels
        df_win['is_attack'] = (df_win['target_risk_score'] > 0.30).astype(int)
        return df_raw, df_win
