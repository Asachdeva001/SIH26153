import os
import yaml
import json
import joblib
import glob
import pandas as pd
import numpy as np
import torch
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.synthetic_generator import SyntheticAttackGenerator
from src.world_model import WorldModelForecaster, BaselineClassifier, BenchmarkEvaluator
from src.parser import TrafficParser, FEATURE_COLUMNS

def grouped_chronological_split(df: pd.DataFrame, group_col: str, test_ratio: float = 0.2):
    """Splits dataframe chronologically while keeping campaigns intact to prevent leakage."""
    if group_col not in df.columns:
        raise ValueError(f"Column {group_col} not found in dataframe.")
        
    groups = df[group_col].unique()
    split_idx = int(len(groups) * (1 - test_ratio))
    
    train_groups = groups[:split_idx]
    test_groups = groups[split_idx:]
    
    train_df = df[df[group_col].isin(train_groups)].copy()
    test_df = df[df[group_col].isin(test_groups)].copy()
    
    return train_df, test_df, list(train_groups), list(test_groups)

def main():
    config_path = "configs/default.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    seed = config['training'].get('seed', 42)
    history_len = config['training'].get('history_len', 4)
    hidden_dim = config['training'].get('hidden_dim', 64)
    epochs = config['training'].get('epochs', 35)
    lr = config['training'].get('learning_rate', 0.005)
    data_dir = config['training'].get('data_dir', 'data/raw/cse-cic-ids2018/')

    np.random.seed(seed)
    torch.manual_seed(seed)

    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    is_synthetic = False

    if csv_files:
        print(f"Found real dataset in {data_dir}. Loading...")
        parser = TrafficParser(window_size_sec=10.0)
        df_list = []
        for file in csv_files[:5]:  # Process up to 5 files
            print(f"Parsing {file}...")
            try:
                df_parsed = parser.parse_csv(file)
                df_win = parser.create_time_windows(df_parsed)
                df_win['attack_campaign'] = os.path.basename(file)
                df_list.append(df_win)
            except Exception as e:
                print(f"Failed to parse {file}: {e}")
        df_win = pd.concat(df_list, ignore_index=True)
        report_file = "models/benchmark_report.json"
        dataset_name = "CSE-CIC-IDS2018"
    else:
        print("*" * 60)
        print("WARNING: Real CIC-IDS-2018 dataset not found.")
        print(f"Path searched: {data_dir}")
        print("DEV/CI MODE: Generating synthetic multi-campaign data.")
        print("*" * 60)
        is_synthetic = True
        report_file = "models/benchmark_report_synthetic.json"
        dataset_name = "Synthetic Dev/CI Fallback"
        
        gen = SyntheticAttackGenerator(seed=seed)
        df_list = []
        campaigns = [
            "APT Multi-Stage Campaign_1", "Benign Intranet Baseline_1", 
            "Ransomware Encryption_1", "DDoS TCP SYN Flood_1",
            "Data Exfiltration (Slow)_1", "Data Exfiltration (Fast)_1",
            "APT Multi-Stage Campaign_2", "Benign Intranet Baseline_2",
            "Ransomware Encryption_2", "DDoS TCP SYN Flood_2"
        ]
        for c in campaigns:
            # We strip the suffix for the generator scenario
            base_scenario = c.rsplit('_', 1)[0]
            _, df_w = gen.generate_scenario(base_scenario, num_windows=20)
            df_w['attack_campaign'] = c
            df_list.append(df_w)
        df_win = pd.concat(df_list, ignore_index=True)

    # 1. SPLIT (Step 2)
    train_df, test_df, train_camps, test_camps = grouped_chronological_split(df_win, group_col='attack_campaign', test_ratio=0.3)
    print(f"Train windows: {len(train_df)}, Test windows: {len(test_df)}")

    os.makedirs("models", exist_ok=True)

    # 2. SHARED SCALER (Step 3)
    X_train_raw = train_df[FEATURE_COLUMNS].values.astype(np.float32)
    mean_ = X_train_raw.mean(axis=0)
    scale_ = X_train_raw.std(axis=0)
    scale_[scale_ == 0] = 1.0

    scaler_data = {'mean_': mean_, 'scale_': scale_}
    joblib.dump(scaler_data, "models/scaler.pkl")

    # 3. JOINT TRAINING (Step 4)
    print("Training WorldModelForecaster...")
    forecaster = WorldModelForecaster(hidden_dim=hidden_dim, history_len=history_len)
    
    # Pre-inject scaler into WorldModel so it uses the shared one
    forecaster.mean_ = mean_
    forecaster.scale_ = scale_
    forecaster.fit(train_df, epochs=epochs, lr=lr)

    print("Training BaselineClassifier...")
    base = BaselineClassifier()
    # Pre-inject scaler into Baseline (even if it doesn't strictly use it yet, we want parity)
    base.mean_ = mean_
    base.scale_ = scale_
    base.fit(train_df)

    # 4. SERIALIZATION (Step 4)
    forecaster.save_model("models/world_model_v1.pth")
    # We will use the custom save_model for baseline shortly, for now just use joblib
    if hasattr(base, 'save_model'):
        base.save_model("models/baseline_lr_v1.pkl")
    else:
        joblib.dump(base, "models/baseline_lr_v1.pkl")

    # 5. BENCHMARK ON HELD-OUT TEST (Step 4)
    y_test_gt = test_df['is_attack'].values if 'is_attack' in test_df.columns else (test_df['target_risk_score'] > 0.30).astype(int)
    
    world_preds = forecaster.predict_k_steps(test_df, K=1)
    world_pred_labels = (np.array(world_preds['risk_trajectory']) > 0.30).astype(int)
    if len(world_pred_labels) < len(y_test_gt):
        pad_len = len(y_test_gt) - len(world_pred_labels)
        world_pred_labels = np.concatenate([np.zeros(pad_len), world_pred_labels])
    
    base_preds = base.predict_proba(test_df)
    
    bench_res = BenchmarkEvaluator.evaluate_comparison(world_pred_labels, base_preds, y_test_gt)

    # PROVENANCE METADATA
    report = {
        "dataset": dataset_name,
        "split_method": "chronological_campaign_grouped",
        "train_campaigns": train_camps,
        "test_campaigns": test_camps,
        "trained_at": datetime.now().isoformat(),
        "metrics": bench_res
    }

    with open(report_file, "w") as f:
        json.dump(report, f, indent=4)
        
    print(f"Training complete. Models and {report_file} saved.")

if __name__ == "__main__":
    main()
