# SIH26153 — Developer Onboarding Guide

**Audit Date:** 2026-09-21

---

## "You Just Joined This Project" — Start Here

### What to Read First (in this order)

1. **`README.md`** — overall project description and setup commands
2. **`docs/audit/00_EXECUTIVE_SUMMARY.md`** — honest assessment of what works and what doesn't
3. **`docs/audit/10_ACTION_PLAN.md`** — your task list, prioritised
4. **`src/world_model.py`** — the core model (PyTorchTransitionLSTM, WorldModelForecaster)
5. **`src/parser.py`** — how data gets ingested and windowed
6. **`app.py`** — the entire UI (one big file, unfortunately)

---

## Tools to Install

```bash
# 1. Python 3.10 or 3.12 (detected from pyc files: 3.12)
python --version

# 2. Git (for history)
git --version

# 3. Install dependencies (note: python-dotenv is MISSING from requirements.txt, add it)
pip install -r requirements.txt
pip install python-dotenv  # until requirements.txt is fixed

# 4. (Optional) For PCAP parsing on Windows:
#    Scapy requires WinPcap or Npcap:
#    https://nmap.org/npcap/ (free, download and install)
```

---

## Exact Verified Setup Commands

```bash
# Clone the repo
git clone https://github.com/Asachdeva001/SIH26153.git
cd SIH26153

# Install deps (add python-dotenv manually if not yet in requirements.txt)
pip install -r requirements.txt

# Configure Kaggle credentials (ask team for new key — old one is compromised)
# Create .env file (DO NOT commit it):
echo "KAGGLE_USERNAME=your_username" > .env
echo "KAGGLE_KEY=your_new_key" >> .env

# Download dataset (requires Kaggle credentials)
python scripts/download_dataset.py

# Train the model (will train on real data if CSV is present, else synthetic)
python scripts/train.py

# Run the app
streamlit run app.py
# Open browser at http://localhost:8501

# Run tests (should show 9 passed)
python -m pytest tests/test_pipeline.py -v
```

---

## How to Run Each Component

### Run Demo (No Dataset Required)
```bash
streamlit run app.py
# App starts with synthetic "APT Multi-Stage Campaign" scenario
# No dataset or training needed — synthetic data auto-generated
```

### Run Training on Synthetic Data (Fast, Dev Mode)
```bash
# Delete or rename the real CSV to force synthetic mode:
python scripts/train.py
# Will detect no CSVs at data/raw/ids-intrusion-csv/ and use synthetic
# Output: models/world_model_v1.pth, models/scaler.pkl, models/benchmark_report_synthetic.json
```

### Run Training on Real CIC-IDS-2018
```bash
# Ensure CSV is at: data/raw/ids-intrusion-csv/02-14-2018.csv
python scripts/train.py
# Output: models/world_model_v1.pth, models/scaler.pkl, models/benchmark_report.json
```

### Run Tests
```bash
python -m pytest tests/test_pipeline.py -v --tb=short
# Expected: 9 passed, ~17 seconds, 1 deprecation warning (scipy L-BFGS-B, harmless)
```

### Generate Synthetic Data Programmatically
```python
from src.synthetic_generator import SyntheticAttackGenerator
gen = SyntheticAttackGenerator(seed=42)
df_raw, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=20)
print(df_win[['window_id', 'ground_truth_stage', 'target_risk_score']].head(20))
```

### Run Inference on a Window
```python
from src.world_model import WorldModelForecaster
forecaster = WorldModelForecaster.load_model("models/world_model_v1.pth")
# df_win must have FEATURE_COLUMNS
result = forecaster.predict_k_steps(df_win.iloc[:5], K=5)
print(result['risk_trajectory'])     # [p1, p2, p3, p4, p5]
print(result['forecast_df'].head())  # K forecasted state vectors
```

---

## The 5 Most Important Things to Understand

1. **The model is trained on SYNTHETIC data** — the committed checkpoint (`world_model_v1.pth`) was trained on `SyntheticAttackGenerator` output, not on real CIC-IDS-2018 traffic. The benchmark report says `dataset: "Synthetic Dev/CI Fallback"`. The first priority is to retrain on real data.

2. **The risk head gets all-zero targets for real data** — when training on the real CSV, `target_risk_score` is not in the windowed DataFrame (it's only produced by the synthetic generator). `world_model.py:66-69` falls through to `np.zeros()`. You MUST map the CIC-IDS-2018 `Label` column to a `target_risk_score` value before training.

3. **K-step rollout is genuinely autoregressive** — `predict_k_steps()` appends the predicted state to `seq_buffer` at each step, so the next forward pass uses the previously *predicted* state. This is the correct world-model mechanism. The rollout code is correct; the model quality is poor.

4. **The evaluation methodology is broken** — `train.py` evaluates the world model by running `predict_k_steps(test_df, K=1)`, getting ONE risk score, padding the rest with zeros, then comparing to the full test set. This produces F1=0.000 for the WM. The correct approach: for each test window T, take the preceding 4 windows as history, predict K steps, compare to `y[T+K]`.

5. **One CDN dependency violates offline requirement** — `app.py:26` has `@import url('https://fonts.googleapis.com/...')`. This must be removed before the submission can claim offline compliance.

---

## The 5 Most Common Mistakes

1. **Assuming the model is trained on real data** — it's not. Always check `models/benchmark_report_synthetic.json` or `models/benchmark_report.json` to see which dataset was used.

2. **Running `python scripts/train.py` and not checking if the real CSV path is correct** — the config at `configs/default.yaml:7` says `data_dir: data/raw/ids-intrusion-csv/`. Make sure the CSV is at exactly that path.

3. **Uploading a large PCAP to the app and expecting fast results** — Scapy's `rdpcap()` loads the entire file into RAM. For a 100 MB PCAP, this may take 30–60 seconds with no progress indicator.

4. **Treating the benchmark tab's 3.5 lead-time bar as real** — it is hard-coded in `app.py:856`. It is not computed from actual inference. See action plan P0-5.

5. **Forgetting that packet-level features (TTL, tcp_win, ip_frag, retrans) are constants for CSV input** — if you're debugging why the model treats two very different CSVs similarly, check that these 5 features are all being filled with defaults rather than real values.

---

## Where to Look When Things Break

| Symptom | Likely Cause | Where to Look |
|---|---|---|
| App crashes on `AttributeError: 'NoneType' has no attribute 'iloc'` | `df_win` is empty (empty file uploaded) | `app.py:472` — add empty check |
| `ModuleNotFoundError: No module named 'dotenv'` | `python-dotenv` not installed | Add to requirements.txt, run `pip install python-dotenv` |
| `FileNotFoundError: models/world_model_v1.pth` | Model not trained yet | Run `python scripts/train.py` |
| Model loads but risk scores all ≈ 0.73 | Trained on synthetic data with broken label target | Retrain after fixing P0-1 |
| `torch.load` raises warning about `weights_only` | PyTorch version conflict | This is a warning, not an error; see P2-9 |
| Streamlit page loads slowly or shows font errors | CDN call blocked by network | See P0-6 — remove Google Fonts CDN |
| Tests fail with `ImportError` | `src/` not on PYTHONPATH | `test_pipeline.py:7` adds the parent dir; ensure pytest is run from project root |
| `KeyError: 'target_risk_score'` in forecast | Column not in df_win (real data mode) | P0-1 fix needed — map Label column |
| Training fails with empty train split | Single CSV file → all goes to test set | P0-2 fix needed — use timestamp-based split for single file |
