import pytest
import numpy as np
import pandas as pd
from backend.src.world_model import BenchmarkEvaluator, BaselineClassifier

def test_benchmark_no_self_comparison():
    # Synthetic test to verify that evaluate_comparison does not rely on model predictions for ground truth
    wm_preds = np.array([0.1, 0.9, 0.2, 0.8])
    base_preds = np.array([0.2, 0.2, 0.2, 0.2])
    gt_binary = np.array([0, 1, 0, 1])
    
    res = BenchmarkEvaluator.evaluate_comparison(wm_preds, base_preds, gt_binary, threshold=0.5)
    assert res['world_model']['f1'] == 1.0
    
    wrong_gt = np.array([0, 0, 0, 0])
    res_wrong = BenchmarkEvaluator.evaluate_comparison(wm_preds, base_preds, wrong_gt, threshold=0.5)
    assert res_wrong['world_model']['f1'] == 0.0, "Evaluator is ignoring ground truth and self-comparing!"

def test_evaluate_k_horizons():
    class DummyModel:
        history_len = 2
        def predict_k_steps(self, history, K=1):
            return {'risk_trajectory': [0.9] * K}
            
    class DummyBase:
        def predict_proba(self, df):
            return np.array([0.1])
            
    test_df = pd.DataFrame({
        'is_attack': [0, 0, 1, 1],
        'target_risk_score': [0.1, 0.1, 0.9, 0.9]
    })
    
    res_k = BenchmarkEvaluator.evaluate_k_horizons(DummyModel(), DummyBase(), test_df, max_k=1, threshold=0.5)
    assert 'k=1' in res_k
    assert res_k['k=1']['world_model']['f1'] == 1.0
