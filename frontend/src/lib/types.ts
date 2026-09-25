export interface TelemetryWindow {
    window_id: number;
    start_sec: number;
    end_sec: number;
    flow_count: number;
    total_packets: number;
    total_bytes: number;
    bytes_per_packet_mean: number;
    bytes_per_packet_max: number;
    flow_duration_mean: number;
    syn_flag_ratio: number;
    ack_flag_ratio: number;
    fin_flag_ratio: number;
    rst_flag_ratio: number;
    psh_flag_ratio: number;
    urg_flag_ratio: number;
    iat_mean: number;
    iat_variance: number;
    iat_max: number;
    ttl_mean: number;
    ttl_std: number;
    tcp_window_mean: number;
    ip_frag_ratio: number;
    unique_src_ips: number;
    unique_dst_ips: number;
    unique_dst_ports: number;
    port_scan_score: number;
    high_port_ratio: number;
    retrans_ratio: number;
    target_risk_score?: number;
    is_attack?: number;
    ground_truth_stage?: string;
}

export interface MitreCustomThresholds {
    exfil_tot_bytes?: number;
    exfil_bytes_pkt?: number;
    c2_iat_var?: number;
    c2_unique_dsts?: number;
    c2_tot_bytes?: number;
    lateral_unique_dsts?: number;
    lateral_high_port_ratio?: number;
    initial_syn_ratio?: number;
    initial_bytes_pkt?: number;
    recon_port_scan_score?: number;
    recon_syn_ratio?: number;
    recon_bytes_pkt?: number;
}

export interface MitreResponse {
    name: string;
    id: string;
    technique: string;
    color: string;
    severity_weight: number;
    confidence: number;
}

export interface XAIAttribution {
    feature: string;
    observed_value: number;
    baseline_value: number;
    shap_value: number;
    abs_shap: number;
    per_timestep: number[];
}

export interface XAIResponse {
    attributions: XAIAttribution[];
    primary_driver: string;
    narrative: string;
}

export interface PlaybookAction {
    step: number;
    action: string;
    type: string;
    status: string;
}

export interface SOCResponse {
    soc_priority_score: number;
    priority_level: string;
    priority_color: string;
    badge_bg: string;
    sla_response: string;
    asset_name: string;
    asset_tier: string;
    asset_weight: number;
    stage_name: string;
    playbook_actions: PlaybookAction[];
}

export interface BenchmarkMetrics {
    f1: number;
    precision: number;
    recall: number;
    fpr: number;
    lead_time_windows: number;
}

export interface BenchmarkResponse {
    world_model: BenchmarkMetrics;
    baseline: BenchmarkMetrics;
    gain_f1_pct: number;
    lead_time_advantage: number;
}
