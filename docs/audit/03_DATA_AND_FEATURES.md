# SIH26153 — Data and Features Audit (v2)

**Audit Date:** 2026-09-23

## Changelog — Re-audit (frontend/backend split + cloud training)
- **Data Location:** Datasets should now be managed in a cloud object store (e.g., AWS S3) for the training pipeline, rather than checked out locally.
- **Code Status:** The parser (`src/parser.py`) and synthetic generator (`src/synthetic_generator.py`) were deleted in recent commits. The findings below refer to the historical implementation that must be restored.
- **API integration:** The new `backend/routers/upload.py` endpoint correctly handles the file upload but performs synchronous disk I/O, which is a production anti-pattern.

---

## 1. Dataset Inventory

**Intended Training Data:**
The `scripts/download_dataset.py` script (now deleted) previously downloaded `02-14-2018.csv` (358 MB) from the `karrtikgupta/cicids2018-clean-and-balanced` Kaggle dataset.

**Target Cloud State:**
For production cloud training, the dataset should be downloaded once to an S3 bucket (e.g., `s3://ntro-sih26153-data/raw/CIC-IDS-2018/`). The cloud training script should stream or download from S3 rather than pulling from Kaggle on every run.

---

## 2. Feature Extraction Coverage (Historical)

The system is designed to use 25 features. Because `src/parser.py` was deleted, this capability is currently **offline**. When restored, it must address the following coverage gaps.

### Flow-Level Features (R3)
| Feature | Supported? | Found In |
|---|---|---|
| Flow count | ✅ | `flow_count` |
| Total packets | ✅ | `total_packets` |
| Total bytes | ✅ | `total_bytes` |
| TCP flag ratios | ✅ | `syn`, `ack`, `fin`, `rst`, `psh`, `urg` ratios |
| IAT stats | ⚠️ Partial | `iat_mean`, `iat_variance`. *Bug in PCAP parser: treats every packet as a new flow.* |
| Port scan score | ✅ | Heuristic based on unique ports |
| Unique IPs | ✅ | `unique_src_ips`, `unique_dst_ips` |

### Packet-Level Features (R4)
| Feature | Supported? | Found In |
|---|---|---|
| TTL stats | ⚠️ CSV Faked | `ttl_mean`, `ttl_std` |
| TCP window sizes | ⚠️ CSV Faked | `tcp_window_mean` |
| IP Fragmentation | ⚠️ CSV Faked | `ip_frag_ratio` |
| Retransmissions | ❌ | *Hardcoded to 0 in both PCAP and CSV paths.* |

---

## 3. The "Fake Data" Problem for CSVs

When the backend processes a CSV file (e.g., CIC-IDS-2018) via `/api/upload`, the data does not contain packet-level features. The previous parser implementation used an `_ensure_column` function to silently fill these with constants:
- `ttl_mean` = 64
- `tcp_window_mean` = 64240
- `ip_frag_ratio` = 0.0
- `retrans_ratio` = 0.0

**Production Impact:** When trained on CSV data, the model learns to ignore these features because they are constant. This is a critical documentation gap that must be disclosed to evaluators.

---

## 4. Production API Data Flow (New Backend)

The new FastAPI endpoint handles data ingestion:

```python
# backend/routers/upload.py
@router.post("/upload", response_model=ScenarioResponse)
async def upload_file(file: UploadFile = File(...)):
    # ...
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # ...
    df_parsed = parser.parse_csv(temp_path)
    # ...
```

**Critical Production Flaws in this implementation:**
1. `upload_file` is an `async def` route.
2. `shutil.copyfileobj` is a blocking synchronous operation.
3. `parser.parse_csv` (parsing potentially 358MB of data) is a blocking CPU-bound operation.
4. Because it is in an `async def`, FastAPI runs it directly on the main event loop, completely freezing the web server for the duration of the upload and parse.
5. **Fix:** Either change `async def` to `def` (so FastAPI runs it in a threadpool) or use `await anyio.to_thread.run_sync(parser.parse_csv, temp_path)`.

---

## 5. Label Engineering Bug

The previous training implementation had a fatal flaw for real data: the CIC-IDS-2018 dataset contains a `Label` column (e.g., "BENIGN", "Bot", "FTP-BruteForce"). However, the model expects a `target_risk_score` (0.0 to 1.0).

Because no mapping function existed, real data resulted in a `KeyError`, which was caught and zero-filled, meaning the model trained against all-zero risk scores.

**Fix Required for Cloud Training:** A mapping dictionary must be applied to the windowed DataFrame before training:
```python
LABEL_TO_RISK = {
    'BENIGN': 0.05,
    'Bot': 0.85,
    'FTP-BruteForce': 0.60,
    # ...
}
```
