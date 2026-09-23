from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ScenarioRequest(BaseModel):
    name: str = "APT Multi-Stage Campaign"
    num_windows: int = 20
    window_size_sec: float = 10.0

class TelemetryWindow(BaseModel):
    window_id: int
    start_sec: float
    end_sec: float
    flow_count: float
    total_packets: float
    total_bytes: float
    bytes_per_packet_mean: float
    bytes_per_packet_max: float
    flow_duration_mean: float
    syn_flag_ratio: float
    ack_flag_ratio: float
    fin_flag_ratio: float
    rst_flag_ratio: float
    psh_flag_ratio: float
    urg_flag_ratio: float
    iat_mean: float
    iat_variance: float
    iat_max: float
    ttl_mean: float
    ttl_std: float
    tcp_window_mean: float
    ip_frag_ratio: float
    unique_src_ips: float
    unique_dst_ips: float
    unique_dst_ports: float
    port_scan_score: float
    high_port_ratio: float
    retrans_ratio: float
    target_risk_score: Optional[float] = None
    is_attack: Optional[int] = None
    ground_truth_stage: Optional[str] = None

class ScenarioResponse(BaseModel):
    windows: List[Dict[str, Any]]
    raw_packets: List[Dict[str, Any]]

class ForecastRequest(BaseModel):
    windows: List[Dict[str, Any]]
    K: int = 5

class ForecastResponse(BaseModel):
    forecast_df: List[Dict[str, Any]]
    risk_trajectory: List[float]

class MitreCustomThresholds(BaseModel):
    exfil_tot_bytes: int = 50000
    exfil_bytes_pkt: int = 1200
    c2_iat_var: float = 0.005
    c2_unique_dsts: int = 2
    c2_tot_bytes: int = 1000
    lateral_unique_dsts: int = 3
    lateral_high_port_ratio: float = 0.4
    initial_syn_ratio: float = 0.3
    initial_bytes_pkt: int = 300
    recon_port_scan_score: float = 3.0
    recon_syn_ratio: float = 0.5
    recon_bytes_pkt: int = 150

class MitreRequest(BaseModel):
    state_dict: Dict[str, Any]
    custom_thresholds: MitreCustomThresholds

class MitreResponse(BaseModel):
    name: str
    id: str
    technique: str
    color: str
    severity_weight: float
    confidence: float

class AssetInfo(BaseModel):
    ip: str
    name: str
    tier: str
    weight: float
    owner: str

class XAIRequest(BaseModel):
    windows: List[Dict[str, Any]]
    asset_ip: str

class XAIAttribution(BaseModel):
    feature: str
    observed_value: float
    baseline_value: float
    shap_value: float
    abs_shap: float
    per_timestep: List[float]

class XAIResponse(BaseModel):
    attributions: List[XAIAttribution]
    primary_driver: str
    narrative: str

class SOCRequest(BaseModel):
    forecast_risk: float
    asset_ip: str
    mitre_stage: MitreResponse

class PlaybookAction(BaseModel):
    step: int
    action: str
    type: str
    status: str

class SOCResponse(BaseModel):
    soc_priority_score: float
    priority_level: str
    priority_color: str
    badge_bg: str
    sla_response: str
    asset_name: str
    asset_tier: str
    asset_weight: float
    stage_name: str
    playbook_actions: List[PlaybookAction]

class BenchmarkRequest(BaseModel):
    windows: List[Dict[str, Any]]
    risk_trajectory: List[float]
    K: int
    threshold: float

class BenchmarkMetrics(BaseModel):
    f1: float
    precision: float
    recall: float
    fpr: float
    lead_time_windows: float

class BenchmarkResponse(BaseModel):
    world_model: BenchmarkMetrics
    baseline: BenchmarkMetrics
    gain_f1_pct: float
    lead_time_advantage: float

class ReportRequest(BaseModel):
    target_asset: Dict[str, Any]
    soc_risk_prioritization: Dict[str, Any]
    scenario: str
    current_window_id: int
    current_risk_score: float
    projected_peak_risk_score: float
    mitre_current_phase: str
    mitre_predicted_phase: str
    forecast_horizon_k: int
    primary_driver: str
    narrative: str
    recommended_playbook: List[PlaybookAction]
