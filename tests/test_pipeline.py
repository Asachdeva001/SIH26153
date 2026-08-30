import pytest
import os
import pandas as pd
import numpy as np

from src.parser import TrafficParser, FEATURE_COLUMNS
from src.synthetic_generator import SyntheticAttackGenerator
from src.world_model import WorldModelForecaster, MITREMapper, BaselineClassifier, BenchmarkEvaluator, AssetCriticalityManager, SOCRiskPrioritizer
from src.explainer import AttackExplainer

def test_synthetic_generator():
    gen = SyntheticAttackGenerator(seed=42)
    df_raw, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=15)

    assert not df_raw.empty, "Raw synthetic telemetry DataFrame should not be empty."
    assert not df_win.empty, "Windowed state DataFrame should not be empty."
    assert abs(len(df_win) - 15) <= 1, "Window count should be within 1 of requested num_windows."
    assert 'target_risk_score' in df_win.columns, "Target risk score column should exist."
    assert 'ground_truth_stage' in df_win.columns, "Ground truth stage column should exist."

def test_traffic_parser():
    parser = TrafficParser(window_size_sec=10.0)
    gen = SyntheticAttackGenerator(seed=42)
    df_raw, _ = gen.generate_scenario("Benign Intranet Baseline", num_windows=10)

    df_parsed = parser.parse_csv(df_raw)
    df_win = parser.create_time_windows(df_parsed)

    for col in FEATURE_COLUMNS:
        assert col in df_win.columns, f"Feature column '{col}' missing from aggregated window DataFrame."

def test_world_model_forecast():
    gen = SyntheticAttackGenerator(seed=42)
    _, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=15)

    forecaster = WorldModelForecaster(history_len=4)
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
    stage_info = MITREMapper.map_state_to_stage(state_sample)

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

    explainer = AttackExplainer()
    xai_res = explainer.explain_window(df_win.iloc[5])

    assert 'attributions' in xai_res, "XAI results should contain attributions."
    assert len(xai_res['attributions']) == 10, "Top 10 feature attributions should be returned."
    assert 'narrative' in xai_res, "XAI results should contain natural language narrative."
