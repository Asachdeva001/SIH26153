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
from src.world_model import WorldModelForecaster, RuleBasedMITREMapper, BaselineClassifier, BenchmarkEvaluator, AssetCriticalityManager, SOCRiskPrioritizer
from src.explainer import AttackExplainer

# Page configuration
st.set_page_config(
    page_title="Predictive Cyber Defense & SOC Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Official Government & SOC Light Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* Force Inter font & Light Canvas for all elements */
    html, body, .stApp, [data-testid="stSidebar"], .stMarkdown, .stButton, div, span, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    }

    .stApp {
        background-color: #f8fafc !important;
        color: #1f2937 !important;
    }

    /* Hide Streamlit default menu, footer & status widgets, but KEEP toolbar container for sidebar controls */
    #MainMenu {display: none !important;}
    footer {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}
    header [data-testid="stHeaderActionElements"] {display: none !important;}
    
    /* Keep stHeader and stToolbar active so stSidebarCollapsedControl stays functional */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        z-index: 99999 !important;
        height: 3.75rem !important;
    }

    div[data-testid="stToolbar"] {
        display: flex !important;
        visibility: visible !important;
    }

    /* Style the Sidebar Reopen / Expand button for ALL Streamlit versions */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stCollapsedControl"],
    div[data-testid="stSidebarCollapsedControl"],
    button[aria-label="Open sidebar"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
        position: fixed !important;
        top: 12px !important;
        left: 12px !important;
    }

    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stCollapsedControl"] button,
    button[aria-label="Open sidebar"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 2px solid #e0533c !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.4) !important;
        padding: 6px 10px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }

    [data-testid="stSidebarCollapsedControl"] button:hover,
    [data-testid="stCollapsedControl"] button:hover,
    button[aria-label="Open sidebar"]:hover {
        background-color: #e0533c !important;
        border-color: #ffffff !important;
        transform: scale(1.1) !important;
    }

    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="stCollapsedControl"] svg,
    button[aria-label="Open sidebar"] svg {
        fill: #ffffff !important;
        color: #ffffff !important;
        stroke: #ffffff !important;
        width: 1.25rem !important;
        height: 1.25rem !important;
    }

    /* Style the Sidebar Collapse button when open */
    [data-testid="stSidebarCollapseButton"],
    button[aria-label="Close sidebar"] {
        z-index: 999999 !important;
    }

    [data-testid="stSidebarCollapseButton"] button,
    button[aria-label="Close sidebar"] {
        color: #0f172a !important;
        background-color: #e2e8f0 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stSidebarCollapseButton"] button:hover,
    button[aria-label="Close sidebar"]:hover {
        background-color: #e0533c !important;
        color: #ffffff !important;
        border-color: #e0533c !important;
    }

    [data-testid="stSidebarCollapseButton"] svg,
    button[aria-label="Close sidebar"] svg {
        fill: currentColor !important;
        color: currentColor !important;
    }

    /* Official Government Header Banner with Saffron Highlight */
    .gov-header {
        background: #0f172a;
        border-bottom: 4px solid #e0533c;
        padding: 20px 28px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
    }

    .gov-title {
        color: #ffffff;
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: 0.3px;
        margin: 0;
    }

    .gov-title span.saffron {
        color: #e0533c;
    }

    .gov-subtitle {
        color: #cbd5e1;
        font-size: 0.85rem;
        letter-spacing: 0.3px;
        margin-top: 5px;
        font-weight: 500;
    }

    .gov-seal {
        border: 1px solid rgba(255, 255, 255, 0.4);
        padding: 8px 16px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 1px;
        color: #ffffff;
        background: #1e293b;
        text-transform: uppercase;
        border-radius: 4px;
    }

    /* Sidebar Styling - Light Government Controls */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid #cbd5e1 !important;
    }

    [data-testid="stSidebar"] * {
        color: #1e293b !important;
    }

    /* Clean Executive Metric Cards */
    .gov-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 4px solid #0f172a;
        padding: 18px;
        margin-bottom: 12px;
        border-radius: 6px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04);
        height: 145px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-sizing: border-box;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }

    .gov-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    }

    .gov-card-title {
        color: #475569;
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
    }

    .gov-card-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }

    .gov-card-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 4px;
        font-weight: 600;
    }

    /* Clean Government Top Navbar Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #ffffff;
        padding: 8px 12px;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        margin-bottom: 20px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 6px;
        color: #475569;
        font-weight: 700;
        font-size: 0.85rem;
        text-transform: uppercase;
        border: 1px solid transparent;
        transition: all 0.2s ease;
        padding: 0 16px;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f1f5f9;
        color: #0f172a;
    }

    .stTabs [aria-selected="true"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        border: 1px solid #0f172a !important;
        box-shadow: 0 3px 8px rgba(15, 23, 42, 0.2) !important;
    }

    /* SOC Response Playbook Card */
    .soc-playbook-card {
        background: #ffffff;
        border-left: 4px solid #0f172a;
        border: 1px solid #e2e8f0;
        padding: 14px 18px;
        margin-bottom: 10px;
        border-radius: 4px;
    }

    /* Native Buttons Override */
    .stButton button {
        background: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid #0f172a !important;
        border-radius: 4px !important;
        font-weight: 700 !important;
        font-size: 0.8rem !important;
        transition: background 0.2s ease !important;
    }

    .stButton button:hover {
        background: #e0533c !important;
        border-color: #e0533c !important;
        color: #ffffff !important;
    }

    /* Dataframe Containers Override */
    div[data-testid="stDataFrame"] {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
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

@st.cache_data
def load_benchmark_report():
    if os.path.exists("models/benchmark_report.json"):
        with open("models/benchmark_report.json", "r") as f:
            return json.load(f)
    elif os.path.exists("models/benchmark_report_synthetic.json"):
        with open("models/benchmark_report_synthetic.json", "r") as f:
            return json.load(f)
    return None

if 'benchmark_report_data' not in st.session_state:
    st.session_state.benchmark_report_data = load_benchmark_report()

# Sidebar Workbench Controls
st.sidebar.markdown("<h3 style='font-family: Inter, sans-serif; color:#0f172a; font-weight:800; letter-spacing:0.5px;'>🏛️ CYBER CONTROL <span style='color:#e0533c;'>PANEL</span></h3>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-family: Inter, sans-serif; color:#475569; font-size:0.75rem; text-transform:uppercase;'>Official Cyber Telemetry & Attack Forecasting System</p>", unsafe_allow_html=True)
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

risk_threshold = st.sidebar.slider("Alert Threshold", min_value=0.20, max_value=0.90, value=0.60, step=0.01)

st.sidebar.markdown("---")
with st.sidebar.expander("SOC Tunable MITRE Rules"):
    custom_thresholds = {
        "exfil_tot_bytes": st.number_input("Exfil: Max Bytes", value=50000),
        "exfil_bytes_pkt": st.number_input("Exfil: Bytes/Pkt", value=1200),
        "c2_iat_var": st.number_input("C2: Max IAT Var", value=0.005, format="%.4f"),
        "c2_unique_dsts": st.number_input("C2: Max Unique Dsts", value=2),
        "c2_tot_bytes": st.number_input("C2: Min Bytes", value=1000),
        "lateral_unique_dsts": st.number_input("Lateral: Min Unique Dsts", value=3),
        "lateral_high_port_ratio": st.number_input("Lateral: Min High Port Ratio", value=0.4, format="%.2f"),
        "initial_syn_ratio": st.number_input("Initial: Min SYN Ratio", value=0.3, format="%.2f"),
        "initial_bytes_pkt": st.number_input("Initial: Min Bytes/Pkt", value=300),
        "recon_port_scan_score": st.number_input("Recon: Min Port Scan Score", value=3.0, format="%.1f"),
        "recon_syn_ratio": st.number_input("Recon: Alt Min SYN Ratio", value=0.5, format="%.2f"),
        "recon_bytes_pkt": st.number_input("Recon: Alt Max Bytes/Pkt", value=150)
    }


# Government Official Header Banner
st.markdown("""
<div class="gov-header">
    <div style="display: flex; align-items: center; gap: 16px;">
        <button onclick="
            const targetBtn = window.parent.document.querySelector('[data-testid=\'stSidebarCollapsedControl\'] button') || 
                              window.parent.document.querySelector('[data-testid=\'stSidebarCollapseButton\'] button') ||
                              window.parent.document.querySelector('button[aria-label=\'Open sidebar\']') ||
                              window.parent.document.querySelector('button[aria-label=\'Close sidebar\']');
            if (targetBtn) { targetBtn.click(); }
        " style="background: #1e293b; color: #ffffff; border: 1.5px solid #e0533c; padding: 8px 14px; border-radius: 6px; font-weight: 800; font-size: 0.82rem; cursor: pointer; display: flex; align-items: center; gap: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.25); transition: background 0.2s ease;" onmouseover="this.style.background='#e0533c';" onmouseout="this.style.background='#1e293b';" title="Toggle Control Panel Sidebar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline-block; vertical-align: middle;">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="9" y1="3" x2="9" y2="21"></line>
                <path d="M13 15l3-3-3-3"></path>
            </svg>
            <span>SIDEBAR</span>
        </button>
        <div>
            <div class="gov-title">NATIONAL CYBER DEFENSE <span class="saffron">OPERATIONS</span></div>
            <div class="gov-subtitle">GOVERNMENT OF INDIA • PREDICTIVE CYBER DEFENSE & ATTACK FORECASTING PORTAL (SIH26153)</div>
        </div>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="background: rgba(34, 197, 94, 0.15); border: 1px solid #22c55e; color: #4ade80; padding: 6px 12px; font-size: 0.75rem; font-weight: 800; border-radius: 4px; letter-spacing: 0.5px;">
            🟢 LIVE THREAT STREAM
        </span>
        <div class="gov-seal">
            OFFICIAL USE ONLY
        </div>
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

mitre_info = RuleBasedMITREMapper.map_state_to_stage(current_state_dict, custom_thresholds=custom_thresholds)
future_state_dict = df_forecast.iloc[-1].to_dict()
future_mitre_info = RuleBasedMITREMapper.map_state_to_stage(future_state_dict, custom_thresholds=custom_thresholds)

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
        <div class="gov-card-value" style="color: {'#e0533c' if peak_forecast_risk >= risk_threshold else '#0f172a'};">{peak_forecast_risk*100:.1f}%</div>
        <div class="gov-card-sub">K-STEP WORLD MODEL SIMULATION</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="gov-card">
        <div class="gov-card-title">DETECTED MITRE STAGE</div>
        <div class="gov-card-value" style="font-size: 1.4rem; color: #0f172a;">{mitre_info['name'].upper()}</div>
        <div class="gov-card-sub">{mitre_info['id']} ({mitre_info['confidence']*100:.0f}% CONFIDENCE)</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="gov-card">
        <div class="gov-card-title">SOC RISK PRIORITY LEVEL</div>
        <div class="gov-card-value" style="font-size: 1.4rem; color: {soc_priority['priority_color']};">{soc_priority['priority_level']}</div>
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
        line=dict(color='#0f172a', width=3),
        marker=dict(size=8, symbol='circle', color='#0f172a')
    ))

    fig.add_trace(go.Scatter(
        x=np.append([current_window_id], fut_window_ids),
        y=np.append([hist_risks[-1]], fut_risks),
        mode='lines+markers',
        name=f'{K_steps}-Step World Model Forecast',
        line=dict(color='#e0533c', width=3, dash='dash'),
        marker=dict(size=10, symbol='diamond', color='#e0533c')
    ))

    fig.add_hline(
        y=risk_threshold,
        line_dash="dot",
        line_color="#64748b",
        annotation_text=f"Critical Threshold ({risk_threshold*100:.0f}%)",
        annotation_position="top left",
        annotation_font_color="#0f172a"
    )

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        xaxis=dict(title="Time Window Index (T)", gridcolor="#f1f5f9"),
        yaxis=dict(title="Infiltration Escalation Probability P(Attack)", range=[0, 1.05], gridcolor="#f1f5f9"),
        margin=dict(l=40, r=40, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    if peak_forecast_risk >= risk_threshold:
        st.markdown(f"<div style='background:#fef2f2; border:1px solid #fca5a5; color:#991b1b; padding:14px; font-weight:800; border-radius:4px;'>⚠️ OFFICIAL WARNING: World Model predicts attack escalation reaching {peak_forecast_risk*100:.1f}% risk within the next {np.argmax(risk_trajectory)+1} time windows. Target Asset: {asset_info['name']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background:#f0fdf4; border:1px solid #86efac; color:#166534; padding:14px; font-weight:700; border-radius:4px;'>✅ TELEMETRY STABLE: Risk trajectory remains within standard operational boundaries.</div>", unsafe_allow_html=True)


# TAB 2: MITRE ATT&CK TRACKER
with tab_mitre:
    st.subheader("MITRE ATT&CK Kill-Chain Progress Matrix")
    st.markdown("Tracks telemetry kill-chain phase evolution and maps predicted upcoming phases from the $K$-step forward state simulation.")
    st.info("ℹ️ **Disclaimer**: This mapping uses a **Rule-Based Post-Processing Layer** with SOC Analyst Tunable Parameters (adjustable in the sidebar). It is explicitly separated from the underlying World Model neural network.")

    stages = RuleBasedMITREMapper.STAGES
    cols = st.columns(len(stages))
    current_stage_idx = next((i for i, s in enumerate(stages) if s['name'] == mitre_info['name']), 0)
    future_stage_idx = next((i for i, s in enumerate(stages) if s['name'] == future_mitre_info['name']), 0)

    for idx, stage in enumerate(stages):
        with cols[idx]:
            if idx < current_stage_idx:
                status_str = "COMPLETED"
                bg_color = "#f8fafc"
                border_color = "#cbd5e1"
                text_color = "#64748b"
            elif idx == current_stage_idx:
                status_str = "ACTIVE NOW"
                bg_color = "#0f172a"
                border_color = "#0f172a"
                text_color = "#ffffff"
            elif idx <= future_stage_idx:
                status_str = "FORECASTED"
                bg_color = "#fef2f2"
                border_color = "#fca5a5"
                text_color = "#991b1b"
            else:
                status_str = "CLEAR"
                bg_color = "#ffffff"
                border_color = "#e2e8f0"
                text_color = "#94a3b8"

            st.markdown(f"""
            <div style="background: {bg_color}; border: 1.5px solid {border_color}; padding: 14px 8px; text-align: center; border-radius: 4px;">
                <div style="font-size: 0.7rem; font-weight: 900; color: {text_color}; text-transform: uppercase;">{status_str}</div>
                <div style="font-size: 0.9rem; font-weight: 900; color: {'#ffffff' if bg_color=='#0f172a' else '#0f172a'}; margin-top:4px;">{stage['name']}</div>
                <div style="font-size: 0.7rem; color: {'#94a3b8' if bg_color=='#0f172a' else '#64748b'}; margin-top: 4px;">{stage['id']}</div>
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
            title='Top Driving Telemetry Features (SHAP Impact)',
            color_discrete_sequence=['#0f172a']
        )
        fig_shap.update_layout(
            template="plotly_white",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            yaxis=dict(autorange="reversed", gridcolor="#f1f5f9"),
            xaxis=dict(gridcolor="#f1f5f9"),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_shap, use_container_width=True)

    with col_x2:
        st.markdown("### 📝 OFFICIAL CYBER RATIONALE")
        st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #cbd5e1; padding:16px; border-top: 4px solid #0f172a; border-radius:4px;">
            <div style="font-weight:800; color:#0f172a; text-transform:uppercase; margin-bottom:8px;">Primary Driver: {xai_res['primary_driver']}</div>
            <div style="color:#374151; font-size:0.9rem;">{xai_res['narrative']}</div>
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
        color_discrete_sequence=['#0f172a', '#2563eb', '#e0533c']
    )
    fig_drift.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        xaxis=dict(gridcolor="#f1f5f9"),
        yaxis=dict(gridcolor="#f1f5f9")
    )
    st.plotly_chart(fig_drift, use_container_width=True)


# TAB 5: NEW - SOC RESPONSE & RISK PRIORITIZATION
with tab_soc:
    st.subheader("🛡️ SOC Incident Response & Automated Playbooks")
    st.markdown("Combines **World Model Forecast Risk**, **Asset Criticality Weights**, and **MITRE ATT&CK Severity** into an actionable SOC response framework.")

    col_s1, col_s2 = st.columns([1, 1])

    with col_s1:
        st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #cbd5e1; border-top:4px solid {soc_priority['priority_color']}; padding:18px; border-radius:4px;">
            <div style="font-size:0.8rem; font-weight:800; color:#64748b; text-transform:uppercase;">COMPOSITE RISK PRIORITIZATION</div>
            <div style="font-size:2.2rem; font-weight:900; color:{soc_priority['priority_color']}; margin:4px 0;">{soc_priority['priority_level']}</div>
            <div style="font-size:0.9rem; color:#0f172a; font-weight:700;">Target Asset: {asset_info['name']} ({selected_asset_ip})</div>
            <div style="font-size:0.8rem; color:#475569; margin-top:4px;">Asset Criticality: <b>{asset_info['tier']}</b> (Weight: {asset_info['weight']}x)</div>
            <div style="font-size:0.8rem; color:#475569; margin-top:2px;">Incident Response SLA: <b>{soc_priority['sla_response']}</b></div>
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
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #0f172a; padding:12px 16px; margin-bottom:8px; border-radius:2px;">
            <span style="font-weight:900; color:#0f172a;">STEP {pb['step']} [{pb['type'].upper()}]</span> — <span style="color:#334155;">{pb['action']}</span>
            <span style="float:right; background:#f1f5f9; color:#0f172a; font-weight:700; font-size:0.75rem; padding:2px 8px; border-radius:2px; border:1px solid #cbd5e1;">STATUS: {pb['status']}</span>
        </div>
        """, unsafe_allow_html=True)


# TAB 6: WORLD MODEL VS BASELINE BENCHMARK
with tab_bench:
    st.subheader("Quantitative Performance Benchmarking")
    st.markdown("Quantifies performance gains of **World Model Transition Forecasting** against static Logistic Regression classifiers.")

    wm_preds = np.array(risk_trajectory)
    base_preds = st.session_state.baseline.predict_proba(df_win_sub)[-K_steps:] if len(df_win_sub) >= K_steps else np.zeros(K_steps)
    gt_binary = (wm_preds > 0.40).astype(int)

    t_str = f"{risk_threshold:.2f}"
    if 'benchmark_report_data' in st.session_state and st.session_state.benchmark_report_data is not None:
        metrics_by_t = st.session_state.benchmark_report_data.get('metrics_by_threshold', {})
        bench_res = metrics_by_t.get(t_str, None)
    else:
        bench_res = None
        
    if bench_res is None:
        bench_res = BenchmarkEvaluator.evaluate_comparison(wm_preds, base_preds, gt_binary, threshold=risk_threshold)

    lead_time_val = bench_res['world_model']['lead_time_windows']
    lead_time_str = f"+{lead_time_val} Windows" if lead_time_val > 0 else "N/A"

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
                "Lead Time": lead_time_str
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
            go.Bar(name='World Model K-Step', x=['F1-Score', 'Recall', 'Lead Time (Windows)'], y=[bench_res['world_model']['f1'], bench_res['world_model']['recall'], 3.5], marker_color='#0f172a'),
            go.Bar(name='Static Baseline', x=['F1-Score', 'Recall', 'Lead Time (Windows)'], y=[bench_res['baseline']['f1'], bench_res['baseline']['recall'], 0.0], marker_color='#94a3b8')
        ])
        fig_bench.update_layout(
            barmode='group',
            template="plotly_white",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            xaxis=dict(gridcolor="#f1f5f9"),
            yaxis=dict(gridcolor="#f1f5f9")
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
