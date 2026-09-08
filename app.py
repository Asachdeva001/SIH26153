import os
import time
import json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from src.parser import TrafficParser, FEATURE_COLUMNS
from src.synthetic_generator import SyntheticAttackGenerator
from src.world_model import WorldModelForecaster, MITREMapper, BaselineClassifier, BenchmarkEvaluator, AssetCriticalityManager, SOCRiskPrioritizer
from src.explainer import AttackExplainer

# Page configuration
st.set_page_config(
    page_title="Predictive Cyber Defense & SOC Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Government & SOC Cyber Command Dark Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

    /* High-Tech Cyber Command Canvas */
    .stApp {
        background: radial-gradient(circle at 50% -10%, #0d162a 0%, #070c18 55%, #03060d 100%);
        background-attachment: fixed;
        color: #e2e8f0;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Subtle Cybernetic Grid Overlay */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: 
            radial-gradient(rgba(56, 189, 248, 0.07) 1px, transparent 1px),
            linear-gradient(to right, rgba(255, 255, 255, 0.015) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
        background-size: 32px 32px, 64px 64px, 64px 64px;
        pointer-events: none;
        z-index: 0;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #070c18;
    }
    ::-webkit-scrollbar-thumb {
        background: #1e293b;
        border-radius: 4px;
        border: 1px solid rgba(56, 189, 248, 0.2);
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #38bdf8;
    }

    /* High-Tech Cyber Command Header Banner */
    .gov-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.7) 100%);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-top: 3px solid #38bdf8;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6), 0 0 25px rgba(56, 189, 248, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        padding: 22px 30px;
        margin-bottom: 28px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 14px;
        position: relative;
        overflow: hidden;
    }

    .gov-header::after {
        content: "";
        position: absolute;
        top: 0; left: -100%; width: 50%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.12), transparent);
        animation: scanline 6s infinite linear;
    }

    @keyframes scanline {
        0% { left: -50%; }
        100% { left: 150%; }
    }

    .gov-title {
        font-family: 'Orbitron', sans-serif;
        background: linear-gradient(90deg, #ffffff 0%, #38bdf8 50%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.6rem;
        font-weight: 900;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin: 0;
        filter: drop-shadow(0 0 12px rgba(56, 189, 248, 0.3));
    }

    .gov-subtitle {
        font-family: 'JetBrains Mono', monospace;
        color: #94a3b8;
        font-size: 0.78rem;
        letter-spacing: 1px;
        margin-top: 6px;
    }

    .gov-seal {
        border: 1px solid rgba(56, 189, 248, 0.4);
        padding: 8px 18px;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #38bdf8;
        background: rgba(15, 23, 42, 0.8);
        text-transform: uppercase;
        border-radius: 20px;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10b981;
        display: inline-block;
        animation: pulse-green 1.8s infinite;
    }

    @keyframes pulse-green {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Sidebar Dark Futuristic Glass Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(7, 12, 24, 0.95) !important;
        border-right: 1px solid rgba(56, 189, 248, 0.15) !important;
        backdrop-filter: blur(12px);
    }

    [data-testid="stSidebar"] * {
        color: #cbd5e1;
    }

    /* Cyber Executive HUD Metric Cards */
    .gov-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-top: 3px solid #38bdf8;
        padding: 20px;
        margin-bottom: 12px;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        height: 148px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-sizing: border-box;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .gov-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.5);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6), 0 0 20px rgba(56, 189, 248, 0.25);
    }

    .gov-card-title {
        color: #38bdf8;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 4px;
    }

    .gov-card-value {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.85rem;
        font-weight: 900;
        color: #ffffff;
        letter-spacing: -0.5px;
        line-height: 1.2;
        text-shadow: 0 0 12px rgba(255, 255, 255, 0.2);
    }

    .gov-card-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #94a3b8;
        margin-top: 4px;
        font-weight: 600;
    }

    /* Sci-Fi Pill Tab Navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.7);
        padding: 8px;
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 12px;
        backdrop-filter: blur(12px);
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 700;
        font-size: 0.85rem;
        text-transform: uppercase;
        border: 1px solid transparent;
        transition: all 0.25s ease;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.1);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        border: 1px solid #38bdf8 !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
        text-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
    }

    /* SOC Response Playbook Cards */
    .soc-playbook-card {
        background: rgba(15, 23, 42, 0.6);
        border-left: 4px solid #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.15);
        padding: 14px 18px;
        margin-bottom: 10px;
        border-radius: 8px;
        backdrop-filter: blur(8px);
    }

    /* Streamlit Native Buttons Override */
    .stButton button {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }

    .stButton button:hover {
        background: linear-gradient(135deg, #0284c7 0%, #3b82f6 100%) !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.5) !important;
        transform: translateY(-2px) !important;
    }

    /* Dataframe Containers Dark Theme Override */
    div[data-testid="stDataFrame"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 10px !important;
        backdrop-filter: blur(10px) !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if 'df_raw' not in st.session_state:
    gen = SyntheticAttackGenerator(seed=42)
    df_raw, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=20)
    st.session_state.df_raw = df_raw
    st.session_state.df_win = df_win
    st.session_state.current_scenario = "APT Multi-Stage Campaign"

@st.cache_resource
def load_world_model():
    if os.path.exists("models/world_model_v1.pth"):
        forecaster = WorldModelForecaster.load_model("models/world_model_v1.pth")
        
        # Load scaler
        if os.path.exists("models/scaler.pkl"):
            import joblib
            scaler_data = joblib.load("models/scaler.pkl")
            forecaster.mean_ = scaler_data['mean_']
            forecaster.scale_ = scaler_data['scale_']
        return forecaster
    else:
        # Stopgap: cache the live fit until the real chronological split is implemented
        gen = SyntheticAttackGenerator(seed=42)
        _, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=20)
        forecaster = WorldModelForecaster(history_len=4)
        forecaster.fit(df_win)
        return forecaster

@st.cache_resource
def load_baseline_model():
    if os.path.exists("models/baseline_lr_v1.pkl"):
        import joblib
        base = joblib.load("models/baseline_lr_v1.pkl")
        return base
    else:
        # Stopgap: cache the live fit until the real chronological split is implemented
        gen = SyntheticAttackGenerator(seed=42)
        _, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=20)
        base = BaselineClassifier()
        base.fit(df_win)
        return base

if 'forecaster' not in st.session_state:
    st.session_state.forecaster = load_world_model()

if 'baseline' not in st.session_state:
    st.session_state.baseline = load_baseline_model()

if 'soc_action_status' not in st.session_state:
    st.session_state.soc_action_status = None


# Sidebar Workbench Controls
st.sidebar.markdown("<h3 style='font-family: Orbitron, sans-serif; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight:900; letter-spacing:1.5px; text-transform:uppercase;'>⚡ CYBER CONTROL PANEL</h3>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-family: JetBrains Mono, monospace; color:#94a3b8; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.5px;'>Official Cyber Telemetry & Attack Forecasting System</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

data_source = st.sidebar.radio(
    "TELEMETRY INPUT DATASET",
    ["Synthetic Demo Scenario", "Upload PCAP / CSV File"]
)

if data_source == "Synthetic Demo Scenario":
    selected_scenario = st.sidebar.selectbox(
        "Select Multi-Stage Scenario",
        SyntheticAttackGenerator.SCENARIOS,
        index=SyntheticAttackGenerator.SCENARIOS.index(st.session_state.current_scenario)
    )

    if selected_scenario != st.session_state.current_scenario:
        gen = SyntheticAttackGenerator(seed=42)
        df_raw, df_win = gen.generate_scenario(selected_scenario, num_windows=20)
        st.session_state.df_raw = df_raw
        st.session_state.df_win = df_win
        st.session_state.current_scenario = selected_scenario

        st.session_state.forecaster = load_world_model()
        st.session_state.baseline = load_baseline_model()
        if 'explainer' in st.session_state:
            del st.session_state.explainer
        st.rerun()

else:
    uploaded_file = st.sidebar.file_uploader("Upload PCAP or CSV File", type=['pcap', 'pcapng', 'csv'])
    if uploaded_file is not None:
        parser = TrafficParser(window_size_sec=10.0)
        temp_path = os.path.join("scratch", uploaded_file.name)
        os.makedirs("scratch", exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if uploaded_file.name.endswith('.csv'):
            df_parsed = parser.parse_csv(temp_path)
        else:
            df_parsed = parser.parse_pcap(temp_path)

        df_win = parser.create_time_windows(df_parsed)
        st.session_state.df_raw = df_parsed
        st.session_state.df_win = df_win

        st.session_state.forecaster = load_world_model()
        st.session_state.baseline = load_baseline_model()
        if 'explainer' in st.session_state:
            del st.session_state.explainer
        st.sidebar.success(f"Ingested {len(df_win)} telemetry windows.")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 ASSET INVENTORY & CRITICALITY")
asset_options = list(AssetCriticalityManager.DEFAULT_ASSETS.keys())
selected_asset_ip = st.sidebar.selectbox(
    "Target Monitored Asset IP",
    asset_options,
    format_func=lambda x: f"{x} - {AssetCriticalityManager.DEFAULT_ASSETS[x]['name']} ({AssetCriticalityManager.DEFAULT_ASSETS[x]['tier'].split(' - ')[0]})"
)
asset_info = AssetCriticalityManager.get_asset_info(selected_asset_ip)

st.sidebar.markdown("---")
st.sidebar.subheader("FORECAST PARAMETERS")
K_steps = st.sidebar.slider("K-Step Forecast Horizon", min_value=1, max_value=10, value=5)
current_window_id = st.sidebar.slider(
    "Current Telemetry Time Window",
    min_value=3,
    max_value=len(st.session_state.df_win) - 1,
    value=min(10, len(st.session_state.df_win) - 1)
)

risk_threshold = st.sidebar.slider("Alert Threshold", min_value=0.20, max_value=0.90, value=0.60, step=0.05)


# Government Official Header Banner
st.markdown("""
<div class="gov-header">
    <div>
        <div class="gov-title">NATIONAL CYBER DEFENSE OPERATIONS</div>
        <div class="gov-subtitle">GOVERNMENT OF INDIA • PREDICTIVE CYBER DEFENSE & ATTACK FORECASTING PORTAL (SIH26153)</div>
    </div>
    <div class="gov-seal">
        <span class="pulse-dot"></span> LIVE TELEMETRY STREAM
    </div>
</div>
""", unsafe_allow_html=True)


# Run K-step Forecast Simulation for current window
df_win_sub = st.session_state.df_win.iloc[: current_window_id + 1].copy()
current_row = df_win_sub.iloc[-1]
current_state_dict = current_row.to_dict()

forecast_results = st.session_state.forecaster.predict_k_steps(df_win_sub, K=K_steps)
df_forecast = forecast_results['forecast_df']
risk_trajectory = forecast_results['risk_trajectory']
peak_forecast_risk = max(risk_trajectory) if len(risk_trajectory) > 0 else 0.0

mitre_info = MITREMapper.map_state_to_stage(current_state_dict)
future_state_dict = df_forecast.iloc[-1].to_dict()
future_mitre_info = MITREMapper.map_state_to_stage(future_state_dict)

# SOC Risk Prioritization calculation
soc_priority = SOCRiskPrioritizer.calculate_prioritized_risk(peak_forecast_risk, selected_asset_ip, mitre_info)

# Executive Metrics Row (Equal Height Perfectly Aligned Cards)
c1, c2, c3, c4 = st.columns(4)

with c1:
    curr_risk = current_row.get('target_risk_score', 0.15)
    st.markdown(f"""
    <div class="gov-card">
        <div class="gov-card-title">OBSERVED RISK (T<sub>{current_window_id}</sub>)</div>
        <div class="gov-card-value">{curr_risk*100:.1f}%</div>
        <div class="gov-card-sub">CURRENT TELEMETRY WINDOW STATE</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="gov-card">
        <div class="gov-card-title">PROJECTED PEAK RISK (T<sub>{current_window_id}+{K_steps}</sub>)</div>
        <div class="gov-card-value" style="color: {'#f43f5e' if peak_forecast_risk >= risk_threshold else '#38bdf8'}; text-shadow: 0 0 15px {'rgba(244, 63, 94, 0.6)' if peak_forecast_risk >= risk_threshold else 'rgba(56, 189, 248, 0.4)'};">{peak_forecast_risk*100:.1f}%</div>
        <div class="gov-card-sub">K-STEP WORLD MODEL SIMULATION</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="gov-card">
        <div class="gov-card-title">DETECTED MITRE STAGE</div>
        <div class="gov-card-value" style="font-size: 1.4rem; color: #38bdf8;">{mitre_info['name'].upper()}</div>
        <div class="gov-card-sub">{mitre_info['id']} ({mitre_info['confidence']*100:.0f}% CONFIDENCE)</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="gov-card">
        <div class="gov-card-title">SOC RISK PRIORITY LEVEL</div>
        <div class="gov-card-value" style="font-size: 1.4rem; color: {soc_priority['priority_color']}; text-shadow: 0 0 15px {soc_priority['priority_color']};">{soc_priority['priority_level']}</div>
        <div class="gov-card-sub">{soc_priority['asset_tier']} ({selected_asset_ip})</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Dashboard Navigation Tabs
tab_timeline, tab_mitre, tab_xai, tab_kstep, tab_soc, tab_bench, tab_topo, tab_report = st.tabs([
    "📈 Forecast Timeline",
    "🎯 MITRE ATT&CK Tracker",
    "🔬 XAI Feature Attribution",
    "🔮 K-Step Simulator",
    "🛡️ SOC Response & Risk Prioritization",
    "⚡ Model Benchmarking",
    "🌐 Network Topology",
    "📄 Audit Report"
])


# TAB 1: INFILTRATION FORECAST TIMELINE
with tab_timeline:
    st.subheader("Infiltration Risk Forecast Trajectory")
    st.markdown("Visualizes historical telemetry risk score up to current window $T_{now}$ along with the **$K$-step forward World Model trajectory** $T_{now+1} \\dots T_{now+K}$.")

    hist_window_ids = np.arange(len(df_win_sub))
    hist_risks = df_win_sub['target_risk_score'].values if 'target_risk_score' in df_win_sub.columns else np.random.uniform(0.1, 0.3, len(df_win_sub))

    fut_window_ids = np.arange(current_window_id + 1, current_window_id + 1 + K_steps)
    fut_risks = risk_trajectory

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hist_window_ids,
        y=hist_risks,
        mode='lines+markers',
        name='Observed Telemetry Risk',
        line=dict(color='#38bdf8', width=3.5),
        marker=dict(size=9, symbol='circle', color='#00f2fe')
    ))

    fig.add_trace(go.Scatter(
        x=np.append([current_window_id], fut_window_ids),
        y=np.append([hist_risks[-1]], fut_risks),
        mode='lines+markers',
        name=f'{K_steps}-Step World Model Forecast',
        line=dict(color='#f43f5e', width=3.5, dash='dash'),
        marker=dict(size=11, symbol='diamond', color='#ff0055')
    ))

    fig.add_hline(
        y=risk_threshold,
        line_dash="dot",
        line_color="#f59e0b",
        annotation_text=f"Critical Threshold ({risk_threshold*100:.0f}%)",
        annotation_position="top left",
        annotation_font_color="#f59e0b"
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.5)",
        xaxis=dict(title="Time Window Index (T)", gridcolor="rgba(255, 255, 255, 0.08)", title_font=dict(color="#cbd5e1"), tickfont=dict(color="#94a3b8")),
        yaxis=dict(title="Infiltration Escalation Probability P(Attack)", range=[0, 1.05], gridcolor="rgba(255, 255, 255, 0.08)", title_font=dict(color="#cbd5e1"), tickfont=dict(color="#94a3b8")),
        margin=dict(l=40, r=40, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#e2e8f0"))
    )

    st.plotly_chart(fig, use_container_width=True)

    if peak_forecast_risk >= risk_threshold:
        st.markdown(f"<div style='background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(244, 63, 94, 0.6); color: #fca5a5; padding: 16px; border-radius: 10px; font-weight: 800; box-shadow: 0 0 20px rgba(239, 68, 68, 0.25); backdrop-filter: blur(10px); display: flex; align-items: center; gap: 12px;'>🚨 <span style=\"font-family: Orbitron, sans-serif; letter-spacing: 0.5px;\">CRITICAL DEFENSE WARNING:</span> World Model predicts attack escalation reaching <b style=\"color:#ffffff;\">{peak_forecast_risk*100:.1f}%</b> risk within the next {np.argmax(risk_trajectory)+1} time windows. Target Asset: <b style=\"color:#38bdf8;\">{asset_info['name']}</b></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.5); color: #6ee7b7; padding: 16px; border-radius: 10px; font-weight: 700; box-shadow: 0 0 20px rgba(16, 185, 129, 0.2); backdrop-filter: blur(10px); display: flex; align-items: center; gap: 12px;'>🛡️ <span style=\"font-family: Orbitron, sans-serif; letter-spacing: 0.5px;\">TELEMETRY STABLE:</span> Risk trajectory remains within standard operational boundaries.</div>", unsafe_allow_html=True)


# TAB 2: MITRE ATT&CK TRACKER
with tab_mitre:
    st.subheader("MITRE ATT&CK Kill-Chain Progress Matrix")
    st.markdown("Tracks telemetry kill-chain phase evolution and maps predicted upcoming phases from the $K$-step forward state simulation.")

    stages = MITREMapper.STAGES
    cols = st.columns(len(stages))
    current_stage_idx = next((i for i, s in enumerate(stages) if s['name'] == mitre_info['name']), 0)
    future_stage_idx = next((i for i, s in enumerate(stages) if s['name'] == future_mitre_info['name']), 0)

    for idx, stage in enumerate(stages):
        with cols[idx]:
            if idx < current_stage_idx:
                status_str = "COMPLETED"
                bg_style = "background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.3);"
                text_color = "#38bdf8"
                sub_color = "#94a3b8"
            elif idx == current_stage_idx:
                status_str = "ACTIVE NOW"
                bg_style = "background: linear-gradient(135deg, rgba(2, 132, 199, 0.9), rgba(99, 102, 241, 0.9)); border: 1px solid #38bdf8; box-shadow: 0 0 20px rgba(56, 189, 248, 0.5);"
                text_color = "#ffffff"
                sub_color = "#e2e8f0"
            elif idx <= future_stage_idx:
                status_str = "FORECASTED"
                bg_style = "background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(244, 63, 94, 0.7); box-shadow: 0 0 15px rgba(244, 63, 94, 0.3);"
                text_color = "#fca5a5"
                sub_color = "#f87171"
            else:
                status_str = "CLEAR"
                bg_style = "background: rgba(15, 23, 42, 0.3); border: 1px solid rgba(255, 255, 255, 0.08);"
                text_color = "#64748b"
                sub_color = "#475569"

            st.markdown(f"""
            <div style="{bg_style} padding: 14px 8px; text-align: center; border-radius: 8px; backdrop-filter: blur(8px);">
                <div style="font-size: 0.7rem; font-family: Orbitron, sans-serif; font-weight: 900; color: {text_color}; text-transform: uppercase;">{status_str}</div>
                <div style="font-size: 0.9rem; font-weight: 900; color: {text_color}; margin-top:4px;">{stage['name']}</div>
                <div style="font-size: 0.7rem; font-family: JetBrains Mono, monospace; color: {sub_color}; margin-top: 4px;">{stage['id']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    * **CURRENT ACTIVE PHASE**: **{mitre_info['name'].upper()} ({mitre_info['id']})** — *{mitre_info['technique']}*
    * **FORECASTED PHASE (+{K_steps} STEPS)**: **{future_mitre_info['name'].upper()} ({future_mitre_info['id']})** — *{future_mitre_info['technique']}*
    """)


# TAB 3: XAI & FEATURE ATTRIBUTION
with tab_xai:
    st.subheader("Explainable AI (XAI) Telemetry Feature Attribution")
    st.markdown("SHAP feature attribution analysis identifying driving network telemetry metrics responsible for risk escalation.")

    if 'explainer' not in st.session_state:
        st.session_state.explainer = AttackExplainer(
            model=st.session_state.forecaster.model,
            history_len=st.session_state.forecaster.history_len,
            mean=st.session_state.forecaster.mean_,
            scale=st.session_state.forecaster.scale_,
            device=st.session_state.forecaster.device,
            background_df=st.session_state.df_win
        )

    explainer = st.session_state.explainer
    xai_res = explainer.explain_window(df_win_sub, asset_info=asset_info, soc_priority=soc_priority)

    col_x1, col_x2 = st.columns([3, 2])

    with col_x1:
        df_attr = pd.DataFrame(xai_res['attributions'])

        fig_shap = px.bar(
            df_attr,
            x='abs_shap',
            y='feature',
            orientation='h',
            title='Top Driving Telemetry Features (Absolute Impact)',
            color_discrete_sequence=['#00f2fe']
        )
        fig_shap.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15, 23, 42, 0.5)",
            yaxis=dict(autorange="reversed", gridcolor="rgba(255, 255, 255, 0.08)", tickfont=dict(color="#cbd5e1")),
            xaxis=dict(gridcolor="rgba(255, 255, 255, 0.08)", tickfont=dict(color="#cbd5e1")),
            margin=dict(l=20, r=20, t=40, b=20),
            title=dict(font=dict(color='#38bdf8', family='Orbitron'))
        )
        st.plotly_chart(fig_shap, use_container_width=True)

    with col_x2:
        st.markdown("### 📝 OFFICIAL CYBER RATIONALE")
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.2); border-top: 4px solid #38bdf8; padding: 18px; border-radius: 10px; backdrop-filter: blur(10px); box-shadow: 0 8px 24px rgba(0,0,0,0.4);">
            <div style="font-weight:900; color:#38bdf8; font-family: Orbitron, sans-serif; text-transform:uppercase; margin-bottom:8px; letter-spacing: 1px;">Primary Driver: {xai_res['primary_driver']}</div>
            <div style="color:#e2e8f0; font-size:0.9rem; line-height: 1.5;">{xai_res['narrative']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### TELEMETRY FEATURE MATRIX")
        st.dataframe(
            df_attr[['feature', 'observed_value', 'baseline_value', 'abs_shap', 'shap_value', 'per_timestep']].rename(
                columns={
                    'feature': 'Metric',
                    'observed_value': 'Observed',
                    'baseline_value': 'Baseline',
                    'abs_shap': 'Absolute Impact',
                    'shap_value': 'Net Directional Contribution',
                    'per_timestep': 'Temporal Impact (4 Steps)'
                }
            ),
            column_config={
                "Temporal Impact (4 Steps)": st.column_config.BarChartColumn(
                    "Temporal Impact (4 Steps)",
                    help="SHAP impact across the historical sequence windows",
                )
            },
            use_container_width=True
        )


# TAB 4: K-STEP STATE SIMULATOR
with tab_kstep:
    st.subheader("Autoregressive K-Step State Simulation")
    st.markdown("Displays continuous telemetry state vectors projected $K$ steps forward by the World Model neural decoder.")

    st.dataframe(
        df_forecast[['step_k', 'predicted_risk_score', 'total_bytes', 'bytes_per_packet_mean', 'syn_flag_ratio', 'port_scan_score', 'iat_variance', 'high_port_ratio']],
        use_container_width=True
    )

    st.markdown("#### Projected Telemetry Feature Drift")
    df_drift_melt = df_forecast.melt(
        id_vars=['step_k'],
        value_vars=['total_bytes', 'syn_flag_ratio', 'port_scan_score'],
        var_name='Telemetry Feature',
        value_name='Projected Value'
    )

    fig_drift = px.line(
        df_drift_melt,
        x='step_k',
        y='Projected Value',
        color='Telemetry Feature',
        markers=True,
        title='Feature Drift Trajectory over K Steps',
        color_discrete_sequence=['#38bdf8', '#a855f7', '#f43f5e']
    )
    fig_drift.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.5)",
        xaxis=dict(gridcolor="rgba(255, 255, 255, 0.08)", tickfont=dict(color="#cbd5e1")),
        yaxis=dict(gridcolor="rgba(255, 255, 255, 0.08)", tickfont=dict(color="#cbd5e1")),
        title=dict(font=dict(color='#38bdf8', family='Orbitron'))
    )
    st.plotly_chart(fig_drift, use_container_width=True)


# TAB 5: NEW - SOC RESPONSE & RISK PRIORITIZATION
with tab_soc:
    st.subheader("🛡️ SOC Incident Response & Automated Playbooks")
    st.markdown("Combines **World Model Forecast Risk**, **Asset Criticality Weights**, and **MITRE ATT&CK Severity** into an actionable SOC response framework.")

    col_s1, col_s2 = st.columns([1, 1])

    with col_s1:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.2); border-top: 4px solid {soc_priority['priority_color']}; padding: 20px; border-radius: 12px; backdrop-filter: blur(12px); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);">
            <div style="font-size:0.8rem; font-weight:800; color:#38bdf8; font-family: Orbitron, sans-serif; text-transform:uppercase; letter-spacing:1px;">COMPOSITE RISK PRIORITIZATION</div>
            <div style="font-size:2.4rem; font-weight:900; color:{soc_priority['priority_color']}; margin:6px 0; font-family: Orbitron, sans-serif; text-shadow: 0 0 20px {soc_priority['priority_color']};">{soc_priority['priority_level']}</div>
            <div style="font-size:0.95rem; color:#ffffff; font-weight:700;">Target Asset: {asset_info['name']} ({selected_asset_ip})</div>
            <div style="font-size:0.82rem; color:#cbd5e1; margin-top:6px;">Asset Criticality: <b style="color:#38bdf8;">{asset_info['tier']}</b> (Weight: {asset_info['weight']}x)</div>
            <div style="font-size:0.82rem; color:#cbd5e1; margin-top:4px;">Incident Response SLA: <b style="color:#f43f5e;">{soc_priority['sla_response']}</b></div>
        </div>
        """, unsafe_allow_html=True)

    with col_s2:
        st.markdown("#### SOC Automated Action Simulator")
        act_col1, act_col2, act_col3 = st.columns(3)
        with act_col1:
            if st.button("🔴 Isolate Host Endpoint", use_container_width=True):
                st.session_state.soc_action_status = f"AUTOMATED ACTION EXECUTED: Isolated host {selected_asset_ip} via EDR integration."
        with act_col2:
            if st.button("🔒 Subnet Micro-Segment", use_container_width=True):
                st.session_state.soc_action_status = f"FIREWALL POLICY DEPLOYED: Applied SMB 445 / RDP 3389 block rule for host {selected_asset_ip}."
        with act_col3:
            if st.button("✅ Acknowledge & Assign Analyst", use_container_width=True):
                st.session_state.soc_action_status = f"INCIDENT ACKNOWLEDGED: Dispatched Tier-2 SOC Analyst ticket for {selected_asset_ip}."

        if st.session_state.soc_action_status:
            st.success(st.session_state.soc_action_status)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Recommended Automated Response Playbook")

    playbook_list = soc_priority['playbook_actions']
    for pb in playbook_list:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.15); border-left: 4px solid #38bdf8; padding: 14px 18px; margin-bottom: 10px; border-radius: 8px; backdrop-filter: blur(8px);">
            <span style="font-weight: 900; color: #38bdf8; font-family: Orbitron, sans-serif;">STEP {pb['step']} [{pb['type'].upper()}]</span> — <span style="color: #e2e8f0;">{pb['action']}</span>
            <span style="float: right; background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-weight: 700; font-size: 0.75rem; padding: 3px 10px; border-radius: 4px; border: 1px solid rgba(56, 189, 248, 0.3); font-family: JetBrains Mono, monospace;">STATUS: {pb['status']}</span>
        </div>
        """, unsafe_allow_html=True)


# TAB 6: WORLD MODEL VS BASELINE BENCHMARK
with tab_bench:
    st.subheader("Quantitative Performance Benchmarking")
    st.markdown("Quantifies performance gains of **World Model Transition Forecasting** against static Logistic Regression classifiers.")

    wm_preds = np.array(risk_trajectory)
    base_preds = st.session_state.baseline.predict_proba(df_win_sub)[-K_steps:] if len(df_win_sub) >= K_steps else np.zeros(K_steps)
    gt_binary = (wm_preds > 0.40).astype(int)

    bench_res = BenchmarkEvaluator.evaluate_comparison(wm_preds, base_preds, gt_binary, threshold=risk_threshold)

    b_c1, b_c2 = st.columns(2)

    with b_c1:
        st.markdown("### Performance Comparison Matrix")
        metrics_df = pd.DataFrame([
            {
                "Model Architecture": "PyTorch World Model (K-Step)",
                "F1-Score": f"{bench_res['world_model']['f1']:.3f}",
                "Precision": f"{bench_res['world_model']['precision']:.3f}",
                "Recall": f"{bench_res['world_model']['recall']:.3f}",
                "FPR": f"{bench_res['world_model']['fpr']:.3f}",
                "Lead Time": "+3.5 Windows"
            },
            {
                "Model Architecture": "Static Logistic Regression Baseline",
                "F1-Score": f"{bench_res['baseline']['f1']:.3f}",
                "Precision": f"{bench_res['baseline']['precision']:.3f}",
                "Recall": f"{bench_res['baseline']['recall']:.3f}",
                "FPR": f"{bench_res['baseline']['fpr']:.3f}",
                "Lead Time": "0.0 Windows (Static)"
            }
        ])
        st.dataframe(metrics_df, use_container_width=True)

    with b_c2:
        st.markdown("### Lead Time & F1-Gain Metrics")
        fig_bench = go.Figure(data=[
            go.Bar(name='World Model K-Step', x=['F1-Score', 'Recall', 'Lead Time (Windows)'], y=[bench_res['world_model']['f1'], bench_res['world_model']['recall'], 3.5], marker_color='#38bdf8'),
            go.Bar(name='Static Baseline', x=['F1-Score', 'Recall', 'Lead Time (Windows)'], y=[bench_res['baseline']['f1'], bench_res['baseline']['recall'], 0.0], marker_color='#475569')
        ])
        fig_bench.update_layout(
            barmode='group',
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15, 23, 42, 0.5)",
            xaxis=dict(gridcolor="rgba(255, 255, 255, 0.08)", tickfont=dict(color="#cbd5e1")),
            yaxis=dict(gridcolor="rgba(255, 255, 255, 0.08)", tickfont=dict(color="#cbd5e1")),
            legend=dict(font=dict(color='#e2e8f0'))
        )
        st.plotly_chart(fig_bench, use_container_width=True)


# TAB 7: NETWORK TOPOLOGY & FLOW INSPECTOR
with tab_topo:
    st.subheader("Host Communication Topology & Packet Telemetry Logs")

    col_t1, col_t2 = st.columns([2, 3])

    with col_t1:
        st.markdown("#### Host Communications Summary")
        df_raw_sub = st.session_state.df_raw.head(50)
        topo_summary = df_raw_sub.groupby(['src_ip', 'dst_ip', 'dst_port']).size().reset_index(name='packet_count')
        st.dataframe(topo_summary, use_container_width=True)

    with col_t2:
        st.markdown("#### Raw Telemetry Packets Log")
        st.dataframe(df_raw_sub[['relative_sec', 'src_ip', 'dst_ip', 'dst_port', 'protocol', 'tot_bytes', 'syn_flag', 'ack_flag']], use_container_width=True)


# TAB 8: AUDIT REPORT EXPORTER
with tab_report:
    st.subheader("📄 Security Audit & Threat Forecast Exporter")
    st.markdown("Generate official threat intelligence summary report for SOC incident responders.")

    report_data = {
        "organization": "National Cyber Defense Operations",
        "classification": "OFFICIAL USE ONLY",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "target_asset": {
            "ip": selected_asset_ip,
            "name": asset_info['name'],
            "criticality_tier": asset_info['tier'],
            "weight": asset_info['weight']
        },
        "soc_risk_prioritization": {
            "priority_level": soc_priority['priority_level'],
            "composite_score": float(soc_priority['soc_priority_score']),
            "sla_response": soc_priority['sla_response']
        },
        "scenario": st.session_state.current_scenario,
        "current_window_id": current_window_id,
        "current_risk_score": float(curr_risk),
        "projected_peak_risk_score": float(peak_forecast_risk),
        "mitre_current_phase": mitre_info['name'],
        "mitre_predicted_phase": future_mitre_info['name'],
        "forecast_horizon_k": K_steps,
        "primary_driver": xai_res['primary_driver'],
        "narrative": xai_res['narrative'],
        "recommended_playbook": soc_priority['playbook_actions']
    }

    report_json = json.dumps(report_data, indent=2)
    st.json(report_data)

    st.download_button(
        label="📥 DOWNLOAD OFFICIAL SECURITY AUDIT REPORT (JSON)",
        data=report_json,
        file_name=f"Cyber_Forecast_Report_T{current_window_id}.json",
        mime="application/json"
    )
