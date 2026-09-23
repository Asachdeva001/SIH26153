# SIH26153 — Data & Features Audit

**Audit Date:** 2026-09-21

---

## Dataset Inventory

| Dataset | Status | Location | Size | Usage |
|---|---|---|---|---|
| **CIC-IDS-2018 (02-14-2018)** | ✅ Present (local only) | `data/raw/ids-intrusion-csv/02-14-2018.csv` | 358 MB | Real data path for training. NOT committed to git. |
| **CTU-13** | ❌ Not present | [NOT FOUND] | — | Column aliases defined in parser but never tested. |
| **UNSW-NB15** | ❌ Not present | [NOT FOUND] | — | Column aliases defined in parser but never tested. |
| **DARPA / LANL Auth** | ❌ Not present | [NOT FOUND] | — | Not referenced anywhere. |
| **Synthetic (internal)** | ✅ Generated at runtime | `src/synthetic_generator.py` | ~200 rows/scenario | 4 scenarios, used for demo and current model training. |

**Dataset provenance note [READ]:** `benchmark_report_synthetic.json:2` states `"dataset": "Synthetic Dev/CI Fallback"`. The saved model checkpoint is trained on synthetic data, not on the 358 MB real CSV.

---

## Feature Coverage Matrix (R3 and R4)

### Flow-Level Features (R3)

| Feature | Status | FEATURE_COLUMNS name | File:Function | Notes |
|---|---|---|---|---|
| src/dst IP & port | ✅ Extracted & used | `unique_src_ips`, `unique_dst_ips`, `unique_dst_ports` | `parser.py:247-249` | Aggregated per window as counts; individual IPs not in state vector (correct — avoids leakage) |
| TCP flag bitmask (SYN) | ✅ Implemented | `syn_flag_ratio` | `parser.py:228,278` | SYN sum / flow count per window |
| TCP flag bitmask (ACK) | ✅ Implemented | `ack_flag_ratio` | `parser.py:229,279` | Same |
| TCP flag bitmask (FIN) | ✅ Implemented | `fin_flag_ratio` | `parser.py:230,280` | Same |
| TCP flag bitmask (RST) | ✅ Implemented | `rst_flag_ratio` | `parser.py:231,281` | Same |
| TCP flag bitmask (PSH) | ✅ Implemented | `psh_flag_ratio` | `parser.py:232,282` | Same |
| TCP flag bitmask (URG) | ✅ Implemented | `urg_flag_ratio` | `parser.py:233,283` | Same |
| Protocol | ⚠️ Partial | Not in FEATURE_COLUMNS | `parser.py:86` | Protocol stored in parsed df but NOT in state vector (windowed). Not a blocker for TCP-focused detection. |
| Bytes/flow | ✅ Implemented | `total_bytes`, `bytes_per_packet_mean`, `bytes_per_packet_max` | `parser.py:263-264,275-276` | |
| Packets/flow | ✅ Implemented | `total_packets`, `flow_count` | `parser.py:272-273` | |
| Flow duration | ✅ Implemented | `flow_duration_mean` | `parser.py:266,277` | Mean of per-row flow_duration values within window |
| IAT mean | ✅ Implemented | `iat_mean` | `parser.py:239,284` | Computed from relative_sec differences within window |
| IAT variance | ✅ Implemented | `iat_variance` | `parser.py:240,285` | `np.var(iats)` within window |
| IAT max | ✅ Implemented | `iat_max` | `parser.py:241,286` | `np.max(iats)` within window |
| Bidirectional flow ratios | ❌ Missing | Not in FEATURE_COLUMNS | — | No fwd_bytes/bwd_bytes split. CIC-IDS-2018 has `Total Length of Fwd Packets` and `Total Length of Bwd Packets` which are mapped to `tot_bytes` only (losing direction). |

### Packet-Level Features (R4)

| Feature | Status (PCAP) | Status (CSV) | FEATURE_COLUMNS name | File:Function | Notes |
|---|---|---|---|---|---|
| TTL values | ✅ PCAP: genuine | ⚠️ CSV: zero-filled | `ttl_mean`, `ttl_std` | `parser.py:134,257-258` | PCAP: `pkt[IP].ttl` extracted. CSV: `_ensure_column(df,'ttl',64)` → constant 64. |
| TCP window size | ✅ PCAP: genuine | ⚠️ CSV: zero-filled | `tcp_window_mean` | `parser.py:153,259` | PCAP: `pkt[TCP].window`. CSV: `_ensure_column(df,'tcp_win',64240)` → constant 64240. |
| IP fragment flags | ✅ PCAP: genuine | ⚠️ CSV: zero-filled | `ip_frag_ratio` | `parser.py:135,260` | PCAP: `pkt[IP].flags.MF or pkt[IP].frag > 0`. CSV: `_ensure_column(df,'ip_frag',0)` → constant 0. |
| Payload size | ✅ PCAP: genuine | ⚠️ CSV: zero-filled | (not in FEATURE_COLUMNS) | `parser.py:154,108` | `payload_bytes` extracted but NOT in FEATURE_COLUMNS. Included in raw df but excluded from state vector. |
| Port-scan signatures | ⚠️ Heuristic only | ⚠️ Heuristic only | `port_scan_score` | `parser.py:252` | `unique_ports / unique_src_ips` — simple heuristic, not entropy-based or sequential/random distinction. No monotonicity check. |
| Retransmission counts | ❌ PCAP: hardcoded 0 | ❌ CSV: hardcoded 0 | `retrans_ratio` | `parser.py:183,261` | PCAP: hardcoded `retrans_count: 0` for every packet. CSV: `_ensure_column(df,'retrans_count',0)`. **Retransmission detection never implemented.** |
| Per-session TTL variance | ✅ Window-level | ⚠️ CSV: always 0 | `ttl_std` | `parser.py:258` | Window-level std across flows. For CSV, TTL is constant 64 → ttl_std=0 always. |

**Critical finding [INFER]:** The CIC-IDS-2018 flow CSV (`02-14-2018.csv`) contains NetFlow-style aggregate features and does NOT contain raw per-packet TTL, TCP window, IP fragment, or retransmission values. Therefore, when training or inferring from this CSV:
- `ttl_mean` = 64.0 (constant)
- `ttl_std` = 0.0 (constant)  
- `tcp_window_mean` = 64240.0 (constant)
- `ip_frag_ratio` = 0.0 (constant)
- `retrans_ratio` = 0.0 (constant)

These 5 features carry **zero information** in CSV mode, reducing the effective feature dimensionality from 25 to 20.

---

## Windowing and State Construction (R6)

| Parameter | Value | Location | Notes |
|---|---|---|---|
| Window size | 10.0 seconds | `configs/default.yaml` (via `TrafficParser(window_size_sec=10.0)`) | `parser.py:45` |
| Window stride | Non-overlapping (= window size) | `parser.py:204` | `np.arange(0, max_time + window_size, window_size)` |
| Aggregation scope | **Global** — all flows in window | `parser.py:212-213` | Not per-host, not per-subnet |
| History length | 4 windows | `configs/default.yaml:4` | 40 seconds of history fed to LSTM |
| State representation | Aggregate feature vector (not graph) | `parser.py:268-297` | No GNN. Simple mean/sum aggregation. |

**Gap:** Global aggregation means that if host A is doing recon and host B is doing benign traffic simultaneously, their signals mix. Per-host windowing would be more discriminative.

---

## Normalisation and Label Engineering (R8)

### Normalisation

| Aspect | Implementation | File:Line | Issue? |
|---|---|---|---|
| Scaler type | Manual z-score (mean/std) | `world_model.py:60-64` | Correct |
| Fit scope | **Fit on training split only** | `train.py:102-105` | ✅ No leakage |
| Persistence | Saved to `models/scaler.pkl` (joblib dict) | `train.py:107-108` | ✅ |
| Inference loading | Loaded from `models/scaler.pkl` before inference | `app.py:314-316` | ✅ |
| Zero-variance features | `scale_[scale_==0] = 1.0` | `world_model.py:62` | ✅ Handles constant features |

### Label Engineering

| Label | Source | Issue? |
|---|---|---|
| `target_risk_score` (continuous, 0-1) | Synthetic: hard-coded per stage in `synthetic_generator.py:200-230`. Real data: **not generated** — `train.py:135` uses `target_risk_score > 0.30` from columns that don't exist in real CSVs → falls back to `is_attack = (target_risk_score > 0.30)` | ⚠️ For real data, there is no `target_risk_score` column, so the fallback `np.zeros()` is used (train.py:69), meaning the risk head trains against all zeros — producing a constant 0 target which explains the poor discrimination |
| `is_attack` (binary) | `target_risk_score > 0.30` or `df['is_attack']` if present | For real CIC-IDS-2018, a `Label` column exists. It is NOT parsed and used. The train script will either find `is_attack` (absent) or `target_risk_score` (absent) → both fall to zeros |
| Attack stage (string) | Hard-coded in `synthetic_generator.py` per window index | No stage annotation from real CIC-IDS-2018 attack timeline |

**🔴 CRITICAL LABEL ENGINEERING BUG:** `train.py:66-69` [READ]:
```python
if 'target_risk_score' in df_windows.columns:
    y_risk = df_windows['target_risk_score'].values.astype(np.float32)
else:
    y_risk = np.zeros(len(df_windows), dtype=np.float32)  # ← ALL ZEROS FOR REAL DATA
```
When training on real CIC-IDS-2018, `target_risk_score` is not in the windowed DataFrame (that column comes only from the synthetic generator), so **the risk head is trained with all-zero targets**. This is why the model produces near-constant, non-discriminative risk scores.

---

## Data Quality and Leakage Analysis

| Issue | Status | Location | Severity |
|---|---|---|---|
| **Random train/test split on time-series** | ✅ Fixed | `train.py:18-32`: campaign-grouped chronological split | 🟢 |
| **Scaler fit on test data** | ✅ Correct | `train.py:102-105`: fit on train split only | 🟢 |
| **Flow ID / IP as features** | ✅ Not present | IPs aggregated as counts; no raw IP values in FEATURE_COLUMNS | 🟢 |
| **Timestamp as feature** | ✅ Not present | `relative_sec` excluded from FEATURE_COLUMNS | 🟢 |
| **Label column leakage** | ✅ Not present | `Label` from CIC-IDS-2018 not in FEATURE_COLUMNS (never parsed into state vector) | 🟢 |
| **Duplicate rows** | ❓ Unverifiable | Cannot run on 358 MB CSV without risking long processing. CIC-IDS-2018 known to have duplicate rows across day files. | 🟠 |
| **Class imbalance handling** | ❌ Missing | No class weighting in LR baseline (`LogisticRegression()` uses no `class_weight`). BCELoss for risk head also unweighted. | 🟠 |
| **NaN/Inf handling** | ⚠️ Partial | `parser.py:72-73` fills NaN timestamps. `ttl_std` guards against NaN (parser.py:288). But `flow_iat_std**2` can produce NaN if all flows have same time (parser.py:244). | 🟠 |
| **Label column in real data** | ❌ Unused | CIC-IDS-2018 `Label` column never parsed into `is_attack` or `target_risk_score` for real training | 🔴 |

---

## PCAP vs CSV Path Analysis

### CSV Path

```
parse_csv() → _ensure_column() fills missing packet-level cols with constants
             → create_time_windows() aggregates flows into 10-sec state vectors
             → packet-level features (TTL, tcp_win, ip_frag, retrans) = CONSTANTS
```

### PCAP Path

```
parse_pcap() → Scapy rdpcap() → per-packet extraction (TTL, TCP flags, win, frag)
             → parse_csv(df) → same as above but now columns are real
             → create_time_windows() aggregates packets into 10-sec state vectors
             → retrans_count = 0 (hardcoded for all packets, never computed)
             → IAT computed within window correctly
             → flow_duration = 0.05 (hardcoded per packet, not a real flow duration)
```

**Key PCAP limitation:** The PCAP parser does not do flow reassembly — it treats each packet as a separate "flow" row. This means:
- `flow_duration` is always 0.05 seconds per packet (hardcoded, `parser.py:173`)
- `flow_iat_mean/std/max` are hardcoded constants (0.01, 0.002, 0.02) for all packets (`parser.py:176-178`)
- Real IAT is then computed from `relative_sec` differences *within the window* (parser.py:236-241), which is packet IAT, not flow IAT — acceptable approximation
- No TCP stream reassembly → no actual retransmission counting
