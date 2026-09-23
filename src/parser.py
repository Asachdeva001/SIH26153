import os
import time
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Union, Any

# Feature column definitions for state vectors S_t
FEATURE_COLUMNS = [
    'flow_count',
    'total_packets',
    'total_bytes',
    'bytes_per_packet_mean',
    'bytes_per_packet_max',
    'flow_duration_mean',
    'syn_flag_ratio',
    'ack_flag_ratio',
    'fin_flag_ratio',
    'rst_flag_ratio',
    'psh_flag_ratio',
    'urg_flag_ratio',
    'iat_mean',
    'iat_variance',
    'iat_max',
    'ttl_mean',
    'ttl_std',
    'tcp_window_mean',
    'ip_frag_ratio',
    'unique_src_ips',
    'unique_dst_ips',
    'unique_dst_ports',
    'port_scan_score',
    'high_port_ratio',
    'retrans_ratio'
]

class PCAPParseError(Exception):
    pass

class TrafficParser:
    """
    Dual-level telemetry parser for raw PCAP and CSV flow datasets.
    Extracts flow-level and packet-level telemetry attributes and
    aggregates them into sequential time windows forming state vectors S_t.
    """
    def __init__(self, window_size_sec: float = 10.0):
        self.window_size_sec = window_size_sec

    def parse_csv(self, file_path_or_df: Union[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Loads and standardizes flow/packet logs from a CSV file or DataFrame.
        Supports CIC-IDS-2018, CTU-13, UNSW-NB15, and custom CSV schemas.
        """
        if isinstance(file_path_or_df, str):
            df = pd.read_csv(file_path_or_df)
        else:
            df = file_path_or_df.copy()

        # Clean column names (strip whitespace, lowercase)
        df.columns = [str(col).strip().lower().replace(' ', '_').replace('/', '_') for col in df.columns]

        # Standardize timestamp
        timestamp_col = None
        for candidate in ['timestamp', 'time', 'first_seen', 'start_time', 'ts']:
            if candidate in df.columns:
                timestamp_col = candidate
                break

        if timestamp_col:
            try:
                df['timestamp_dt'] = pd.to_datetime(df[timestamp_col], errors='coerce')
                # Fill NaNs if any date parsing failed
                if df['timestamp_dt'].isna().any():
                    df['timestamp_dt'] = df['timestamp_dt'].fillna(method='ffill').fillna(pd.Timestamp.now())
                df['relative_sec'] = (df['timestamp_dt'] - df['timestamp_dt'].min()).dt.total_seconds()
            except Exception:
                df['relative_sec'] = np.linspace(0, len(df) * 0.5, len(df))
        else:
            # Fallback if no timestamp present
            df['relative_sec'] = np.linspace(0, len(df) * 0.5, len(df))

        # Standardize core fields
        self._ensure_column(df, 'src_ip', '192.168.1.100')
        self._ensure_column(df, 'dst_ip', '10.0.0.1')
        self._ensure_column(df, 'src_port', 80)
        self._ensure_column(df, 'dst_port', 80)
        self._ensure_column(df, 'protocol', 6)  # TCP default

        # TCP Flags
        self._ensure_column(df, 'syn_flag', 0)
        self._ensure_column(df, 'ack_flag', 0)
        self._ensure_column(df, 'fin_flag', 0)
        self._ensure_column(df, 'rst_flag', 0)
        self._ensure_column(df, 'psh_flag', 0)
        self._ensure_column(df, 'urg_flag', 0)

        # Flow metrics
        self._ensure_column(df, 'flow_duration', 0.1)
        self._ensure_column(df, 'tot_bytes', 500)
        self._ensure_column(df, 'tot_pkts', 5)
        self._ensure_column(df, 'flow_iat_mean', 0.02)
        self._ensure_column(df, 'flow_iat_std', 0.005)
        self._ensure_column(df, 'flow_iat_max', 0.05)

        # Packet-level attributes
        self._ensure_column(df, 'ttl', 64)
        self._ensure_column(df, 'tcp_win', 64240)
        self._ensure_column(df, 'ip_frag', 0)
        self._ensure_column(df, 'payload_bytes', 100)
        self._ensure_column(df, 'retrans_count', 0)

        return df

    def parse_pcap(self, pcap_path: str) -> pd.DataFrame:
        """
        Parses raw .pcap or .pcapng files into flow/packet telemetry DataFrames.
        Attempts scapy ingestion, with fallback packet reader.
        """
        packets_data = []

        try:
            from scapy.all import rdpcap, IP, TCP, UDP
            scapy_pkts = rdpcap(pcap_path)
            base_time = None

            for pkt in scapy_pkts:
                if base_time is None:
                    base_time = float(pkt.time)

                rel_time = float(pkt.time) - base_time
                pkt_size = len(pkt)
                src_ip = pkt[IP].src if IP in pkt else "127.0.0.1"
                dst_ip = pkt[IP].dst if IP in pkt else "127.0.0.1"
                proto = pkt[IP].proto if IP in pkt else 0
                ttl = pkt[IP].ttl if IP in pkt else 64
                ip_frag = 1 if (IP in pkt and pkt[IP].flags.MF or (IP in pkt and pkt[IP].frag > 0)) else 0

                src_port = 0
                dst_port = 0
                syn = ack = fin = rst = psh = urg = 0
                tcp_win = 0
                payload_len = 0

                if TCP in pkt:
                    src_port = pkt[TCP].sport
                    dst_port = pkt[TCP].dport
                    flags = str(pkt[TCP].flags)
                    syn = 1 if 'S' in flags else 0
                    ack = 1 if 'A' in flags else 0
                    fin = 1 if 'F' in flags else 0
                    rst = 1 if 'R' in flags else 0
                    psh = 1 if 'P' in flags else 0
                    urg = 1 if 'U' in flags else 0
                    tcp_win = pkt[TCP].window
                    payload_len = len(pkt[TCP].payload)
                elif UDP in pkt:
                    src_port = pkt[UDP].sport
                    dst_port = pkt[UDP].dport
                    payload_len = len(pkt[UDP].payload)

                packets_data.append({
                    'relative_sec': rel_time,
                    'src_ip': src_ip,
                    'dst_ip': dst_ip,
                    'src_port': src_port,
                    'dst_port': dst_port,
                    'protocol': proto,
                    'syn_flag': syn,
                    'ack_flag': ack,
                    'fin_flag': fin,
                    'rst_flag': rst,
                    'psh_flag': psh,
                    'urg_flag': urg,
                    'flow_duration': 0.05,
                    'tot_bytes': pkt_size,
                    'tot_pkts': 1,
                    'flow_iat_mean': 0.01,
                    'flow_iat_std': 0.002,
                    'flow_iat_max': 0.02,
                    'ttl': ttl,
                    'tcp_win': tcp_win,
                    'ip_frag': ip_frag,
                    'payload_bytes': payload_len,
                    'retrans_count': 0
                })
        except Exception as e:
            from scapy.error import Scapy_Exception
            import struct
            if isinstance(e, (Scapy_Exception, struct.error, EOFError)):
                raise PCAPParseError(f"Could not parse this PCAP file: {e}") from e
            raise PCAPParseError(f"PCAP parsing failed: {e}") from e

        df = pd.DataFrame(packets_data)
        return self.parse_csv(df)

    def create_time_windows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates raw telemetry DataFrame into continuous sequential time windows [T_0, T_1, ... T_n].
        Returns DataFrame where each row represents a high-dimensional state vector S_t.
        """
        if df.empty:
            return pd.DataFrame(columns=['window_id', 'start_sec', 'end_sec'] + FEATURE_COLUMNS)

        max_time = df['relative_sec'].max()
        window_bins = np.arange(0, max_time + self.window_size_sec, self.window_size_sec)
        if len(window_bins) < 2:
            window_bins = np.array([0, self.window_size_sec])

        df['window_idx'] = pd.cut(df['relative_sec'], bins=window_bins, labels=False, include_lowest=True)
        df['window_idx'] = df['window_idx'].fillna(0).astype(int)

        window_records = []
        grouped = df.groupby('window_idx')

        total_windows = int(np.ceil(max_time / self.window_size_sec)) + 1
        total_windows = max(total_windows, df['window_idx'].max() + 1)

        from tqdm import tqdm
        for w_idx in tqdm(range(total_windows), desc="Aggregating Windows"):
            start_t = w_idx * self.window_size_sec
            end_t = (w_idx + 1) * self.window_size_sec

            if w_idx in grouped.groups:
                w_df = grouped.get_group(w_idx)
                n_pkts = len(w_df)
                tot_pkts = w_df['tot_pkts'].sum() if 'tot_pkts' in w_df else n_pkts
                tot_bytes = w_df['tot_bytes'].sum()

                syn_sum = w_df['syn_flag'].sum()
                ack_sum = w_df['ack_flag'].sum()
                fin_sum = w_df['fin_flag'].sum()
                rst_sum = w_df['rst_flag'].sum()
                psh_sum = w_df['psh_flag'].sum()
                urg_sum = w_df['urg_flag'].sum()

                # IAT calculations
                rel_times = w_df['relative_sec'].sort_values().values
                if len(rel_times) > 1:
                    iats = np.diff(rel_times)
                    iat_m = float(np.mean(iats))
                    iat_v = float(np.var(iats))
                    iat_mx = float(np.max(iats))
                else:
                    iat_m = float(w_df['flow_iat_mean'].mean()) if 'flow_iat_mean' in w_df else 0.05
                    iat_v = float(w_df['flow_iat_std'].mean()**2) if 'flow_iat_std' in w_df else 0.001
                    iat_mx = float(w_df['flow_iat_max'].mean()) if 'flow_iat_max' in w_df else 0.1

                unique_srcs = w_df['src_ip'].nunique()
                unique_dsts = w_df['dst_ip'].nunique()
                unique_ports = w_df['dst_port'].nunique()

                # Port scan heuristic score: high unique destination ports per src IP
                port_scan_score = float(unique_ports / max(1, unique_srcs)) if unique_srcs > 0 else 0.0

                high_ports = (w_df['dst_port'] > 1024).sum()
                high_port_ratio = float(high_ports / max(1, n_pkts))

                ttl_m = float(w_df['ttl'].mean())
                ttl_s = float(w_df['ttl'].std()) if n_pkts > 1 else 0.0
                tcp_win_m = float(w_df['tcp_win'].mean())
                ip_frag_r = float(w_df['ip_frag'].sum() / max(1, n_pkts))
                retrans_r = float(w_df['retrans_count'].sum() / max(1, n_pkts))

                bytes_pkt_mean = float(tot_bytes / max(1, tot_pkts))
                bytes_pkt_max = float(w_df['tot_bytes'].max())

                flow_dur_mean = float(w_df['flow_duration'].mean())

                rec = {
                    'window_id': w_idx,
                    'start_sec': start_t,
                    'end_sec': end_t,
                    'flow_count': n_pkts,
                    'total_packets': float(tot_pkts),
                    'total_bytes': float(tot_bytes),
                    'bytes_per_packet_mean': bytes_pkt_mean,
                    'bytes_per_packet_max': bytes_pkt_max,
                    'flow_duration_mean': flow_dur_mean,
                    'syn_flag_ratio': float(syn_sum / max(1, n_pkts)),
                    'ack_flag_ratio': float(ack_sum / max(1, n_pkts)),
                    'fin_flag_ratio': float(fin_sum / max(1, n_pkts)),
                    'rst_flag_ratio': float(rst_sum / max(1, n_pkts)),
                    'psh_flag_ratio': float(psh_sum / max(1, n_pkts)),
                    'urg_flag_ratio': float(urg_sum / max(1, n_pkts)),
                    'iat_mean': iat_m,
                    'iat_variance': iat_v,
                    'iat_max': iat_mx,
                    'ttl_mean': ttl_m,
                    'ttl_std': ttl_s if not np.isnan(ttl_s) else 0.0,
                    'tcp_window_mean': tcp_win_m,
                    'ip_frag_ratio': ip_frag_r,
                    'unique_src_ips': float(unique_srcs),
                    'unique_dst_ips': float(unique_dsts),
                    'unique_dst_ports': float(unique_ports),
                    'port_scan_score': port_scan_score,
                    'high_port_ratio': high_port_ratio,
                    'retrans_ratio': retrans_r
                }
            else:
                # Empty window baseline interpolation
                rec = {
                    'window_id': w_idx,
                    'start_sec': start_t,
                    'end_sec': end_t,
                    'flow_count': 0,
                    'total_packets': 0.0,
                    'total_bytes': 0.0,
                    'bytes_per_packet_mean': 0.0,
                    'bytes_per_packet_max': 0.0,
                    'flow_duration_mean': 0.0,
                    'syn_flag_ratio': 0.0,
                    'ack_flag_ratio': 0.0,
                    'fin_flag_ratio': 0.0,
                    'rst_flag_ratio': 0.0,
                    'psh_flag_ratio': 0.0,
                    'urg_flag_ratio': 0.0,
                    'iat_mean': 1.0,
                    'iat_variance': 0.0,
                    'iat_max': 1.0,
                    'ttl_mean': 64.0,
                    'ttl_std': 0.0,
                    'tcp_window_mean': 64240.0,
                    'ip_frag_ratio': 0.0,
                    'unique_src_ips': 0.0,
                    'unique_dst_ips': 0.0,
                    'unique_dst_ports': 0.0,
                    'port_scan_score': 0.0,
                    'high_port_ratio': 0.0,
                    'retrans_ratio': 0.0
                }
            window_records.append(rec)

        return pd.DataFrame(window_records)

    def _ensure_column(self, df: pd.DataFrame, target: str, default_val: Any) -> None:
        """Helper to map alternative column names to standardized names."""

        if target in df.columns:
            return

        mappings = {
            'src_ip': ['source_ip', 'srcip', 'sa', 'src_addr', 'src'],
            'dst_ip': ['destination_ip', 'dstip', 'da', 'dst_addr', 'dst'],
            'src_port': ['source_port', 'srcport', 'sp', 'sport'],
            'dst_port': ['destination_port', 'dstport', 'dp', 'dport'],
            'protocol': ['proto', 'prot'],
            'syn_flag': ['syn_flag_count', 'syn', 'fwd_psh_flags'],
            'ack_flag': ['ack_flag_count', 'ack'],
            'fin_flag': ['fin_flag_count', 'fin'],
            'rst_flag': ['rst_flag_count', 'rst'],
            'psh_flag': ['psh_flag_count', 'psh'],
            'urg_flag': ['urg_flag_count', 'urg'],
            'flow_duration': ['duration', 'flow_duration_ms', 'flow_dur'],
            'tot_bytes': ['total_length_of_fwd_packets', 'tot_len_fwd_pkts', 'bytes', 'length', 'pkt_len'],
            'tot_pkts': ['total_fwd_packets', 'tot_pkts', 'packets', 'pkt_cnt'],
            'flow_iat_mean': ['flow_iat_mean', 'iat_mean', 'fwd_iat_mean'],
            'flow_iat_std': ['flow_iat_std', 'iat_std', 'fwd_iat_std'],
            'flow_iat_max': ['flow_iat_max', 'iat_max', 'fwd_iat_max'],
            'ttl': ['ip_ttl', 'time_to_live'],
            'tcp_win': ['init_win_bytes_forward', 'window_size'],
            'payload_bytes': ['payload_len', 'pkt_payload', 'b_pkt_mean']
        }

        found = False
        if target in mappings:
            for alt in mappings[target]:
                if alt in df.columns:
                    df[target] = df[alt]
                    found = True
                    break

        if not found:
            df[target] = default_val


