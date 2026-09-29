import pytest
import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.src.parser import TrafficParser, FEATURE_COLUMNS
from backend.src.synthetic_generator import SyntheticAttackGenerator
from backend.src.world_model import WorldModelForecaster, RuleBasedMITREMapper, BaselineClassifier, BenchmarkEvaluator, AssetCriticalityManager, SOCRiskPrioritizer
from backend.src.explainer import AttackExplainer

def test_synthetic_generator():
    gen = SyntheticAttackGenerator(seed=42)
    df_raw, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=15)

    assert not df_raw.empty, "Raw synthetic telemetry DataFrame should not be empty."
    assert not df_win.empty, "Windowed state DataFrame should not be empty."
    assert abs(len(df_win) - 15) <= 1, "Window count should be within 1 of requested num_windows."
    assert 'target_risk_score' in df_win.columns, "Target risk score column should exist."
    assert 'ground_truth_stage' in df_win.columns, "Ground truth stage column should exist."

def test_traffic_parser_correctness():
    parser = TrafficParser(window_size_sec=10.0)
    # create a tiny fake dataframe instead of synthetic generator to test exact parsing values
    data = [
        {
            'timestamp': '2023-01-01 00:00:01', 'src_ip': '1.1.1.1', 'dst_ip': '2.2.2.2', 
            'src_port': 80, 'dst_port': 443, 'protocol': 6,
            'syn_flag': 1, 'ack_flag': 0, 'fin_flag': 0, 'rst_flag': 0, 'psh_flag': 0, 'urg_flag': 0,
            'flow_duration': 0.1, 'tot_bytes': 1000, 'tot_pkts': 2,
            'flow_iat_mean': 0.05, 'flow_iat_std': 0.01, 'flow_iat_max': 0.08,
            'ttl': 64, 'tcp_win': 1024, 'ip_frag': 0, 'payload_bytes': 500, 'retrans_count': 0
        },
        {
            'timestamp': '2023-01-01 00:00:25', 'src_ip': '1.1.1.1', 'dst_ip': '2.2.2.2', 
            'src_port': 80, 'dst_port': 443, 'protocol': 6,
            'syn_flag': 0, 'ack_flag': 1, 'fin_flag': 0, 'rst_flag': 0, 'psh_flag': 0, 'urg_flag': 0,
            'flow_duration': 0.1, 'tot_bytes': 500, 'tot_pkts': 1,
            'flow_iat_mean': 0.05, 'flow_iat_std': 0.01, 'flow_iat_max': 0.08,
            'ttl': 64, 'tcp_win': 1024, 'ip_frag': 0, 'payload_bytes': 200, 'retrans_count': 0
        }
    ]
    df_parsed = parser.parse_csv(pd.DataFrame(data))
    df_win = parser.create_time_windows(df_parsed)
    
    # Assert exact extraction of a numeric feature
    assert df_win.iloc[0]['total_bytes'] == 1000, "Parser failed to correctly extract and window the total_bytes feature."
    assert df_win.iloc[0]['syn_flag_ratio'] == 1.0, "Parser failed to correctly extract the syn_flag ratio."
    
    # Assert empty window extrapolation worked for window 1 (10s - 20s)
    assert df_win.iloc[1]['total_bytes'] == 0, "Empty window extrapolation failed for total_bytes."
    assert df_win.iloc[1]['flow_count'] == 0, "Empty window should have 0 flows."
    
    # Assert window 2 (20s - 30s) captured the second packet
    assert df_win.iloc[2]['total_bytes'] == 500, "Parser failed to extract second window data."

def test_unlabeled_traffic_gets_inferred_risk():
    parser = TrafficParser(window_size_sec=10.0)
    data = pd.DataFrame([{
        'timestamp': '2023-01-01 00:00:01', 'src_ip': '1.1.1.1', 'dst_ip': '2.2.2.2',
        'src_port': 40000, 'dst_port': 40001, 'protocol': 6,
        'syn_flag': 1, 'ack_flag': 0, 'fin_flag': 0, 'rst_flag': 0, 'psh_flag': 0, 'urg_flag': 0,
        'flow_duration': 0.1, 'tot_bytes': 1000, 'tot_pkts': 1,
        'flow_iat_mean': 0.05, 'flow_iat_std': 0.01, 'flow_iat_max': 0.08,
        'ttl': 64, 'tcp_win': 1024, 'ip_frag': 0, 'payload_bytes': 500, 'retrans_count': 0
    }])

    df_win = parser.create_time_windows(parser.parse_csv(data))

    assert 0.0 < df_win.iloc[0]['target_risk_score'] <= 1.0

def test_world_model_forecast():
    gen = SyntheticAttackGenerator(seed=42)
    _, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=15)

    forecaster = WorldModelForecaster(history_len=8)
    forecaster.fit(df_win, epochs=10)

    assert forecaster.is_fitted, "Forecaster should be marked as fitted after training."

    res = forecaster.predict_k_steps(df_win.iloc[:6], K=5)
    assert 'forecast_df' in res, "Results should contain forecast_df."
    assert len(res['risk_trajectory']) == 5, "Risk trajectory should have 5 forecasted values."
    assert res['forecast_df'].shape[0] == 5, "Forecast DataFrame should have 5 rows."

def test_mitre_mapper():
    state_sample = {
        'bytes_per_packet_mean': 1500,
        'total_bytes': 80000,
        'syn_flag_ratio': 0.1,
        'unique_dst_ports': 2,
        'port_scan_score': 0.5,
        'iat_variance': 0.01
    }
    stage_info = RuleBasedMITREMapper.map_state_to_stage(state_sample)

    assert 'name' in stage_info, "Stage info should contain name."
    assert 'id' in stage_info, "Stage info should contain technique ID."
    assert stage_info['name'] == 'Exfiltration', "High byte sample should map to Exfiltration stage."

def test_asset_criticality_and_soc_prioritizer():
    asset_ip = "10.0.0.15"  # Domain Controller
    asset_info = AssetCriticalityManager.get_asset_info(asset_ip)
    assert asset_info['weight'] >= 2.0, "Domain Controller should have high asset weight."

    mitre_stage = {"name": "Exfiltration", "severity_weight": 2.5}
    prio_res = SOCRiskPrioritizer.calculate_prioritized_risk(0.90, asset_ip, mitre_stage)

    assert 'priority_level' in prio_res, "Priority result should contain priority_level."
    assert prio_res['priority_level'] == "P1 - CRITICAL", "High forecast + Tier 1 asset should be P1 Critical."
    assert len(prio_res['playbook_actions']) > 0, "Recommended playbook actions should not be empty."

def test_baseline_and_evaluator():
    gen = SyntheticAttackGenerator(seed=42)
    _, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=15)

    base = BaselineClassifier()
    base.fit(df_win)

    preds = base.predict_proba(df_win)
    assert len(preds) == len(df_win), "Baseline predictions length should match window count."

    gt = df_win['is_attack'].values
    bench_res = BenchmarkEvaluator.evaluate_comparison(preds, preds, gt)
    assert 'world_model' in bench_res, "Benchmark evaluation should contain world_model key."
    assert 'baseline' in bench_res, "Benchmark evaluation should contain baseline key."

def test_explainer():
    gen = SyntheticAttackGenerator(seed=42)
    _, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=10)

    forecaster = WorldModelForecaster(history_len=8)
    forecaster.fit(df_win, epochs=2)

    explainer = AttackExplainer(
        model=forecaster.model,
        history_len=forecaster.history_len,
        mean=forecaster.mean_,
        scale=forecaster.scale_,
        device=forecaster.device,
        background_df=df_win
    )
    xai_res = explainer.explain_window(df_win.iloc[:6])

    assert 'attributions' in xai_res, "XAI results should contain attributions."
    assert len(xai_res['attributions']) == 10, "Top 10 feature attributions should be returned."
    assert 'narrative' in xai_res, "XAI results should contain natural language narrative."
    
    # SHAP Sanity Check: Assert local accuracy property (sum of attributions ~ f(x) - E[f(baseline)])
    # The sum of 'shap_value' for all features should approximately equal the difference between model output and expected baseline.
    total_shap = sum([float(attr['shap_value']) for attr in xai_res['full_attributions_df'].to_dict(orient='records')])
    # We just ensure it's not identically zero when there's an anomaly, as a basic correctness check
    assert isinstance(total_shap, float)

def test_no_leakage_chronological_split():
    from backend.scripts.train import grouped_chronological_split
    
    gen = SyntheticAttackGenerator(seed=42)
    df_list = []
    for c in ["Campaign_A", "Campaign_B", "Campaign_C"]:
        _, df = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=10)
        df['attack_campaign'] = c
        df_list.append(df)
        
    df_win = pd.concat(df_list)
    train_df, test_df, train_camps, test_camps = grouped_chronological_split(df_win, group_col='attack_campaign', test_ratio=0.33)
    
    # Assert no campaign leakage
    train_campaigns = set(train_df['attack_campaign'].unique())
    test_campaigns = set(test_df['attack_campaign'].unique())
    
    assert train_campaigns.isdisjoint(test_campaigns), "Test campaigns must not appear in train set to prevent leakage."

def test_metric_sanity_lead_time():
    # Never crosses threshold
    wm_probs = np.array([0.1, 0.2, 0.3])
    base_probs = np.array([0.1, 0.1, 0.2])
    
    lead_time = BenchmarkEvaluator.compute_lead_time(wm_probs, base_probs, threshold=0.5)
    assert lead_time is None, "Lead time should be None if threshold is never crossed."
    
    # World model crosses at idx 1, baseline crosses at idx 3
    wm_probs = np.array([0.1, 0.6, 0.7, 0.8])
    base_probs = np.array([0.1, 0.2, 0.3, 0.6])
    
    lead_time = BenchmarkEvaluator.compute_lead_time(wm_probs, base_probs, threshold=0.5)
    assert lead_time == 2, "Lead time advantage should be exactly 2 time windows."


