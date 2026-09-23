# SIH26153 — Open Questions & Ambiguities

**Audit Date:** 2026-09-21

---

## Team Decisions Required

These questions need explicit answers from the team before implementation proceeds. For each, the auditor notes the likely best answer and the consequence of each choice.

---

### Q1. Primary Training Dataset: Which Day Files Will You Download?

**Context:** `scripts/download_dataset.py` downloads only `02-14-2018.csv` (358 MB, one day). The `grouped_chronological_split()` in `train.py` groups by filename — with a single file, the split collapses. CIC-IDS-2018 has 10 day-files available (Feb 14–23, 2018), covering different attack types.

**Options:**
- A) Download 3+ day files (e.g., Feb 14, 15, 20, 22) — enables multi-day chronological split, covers: DoS, Brute Force, Web Attacks, Bot/C2, Infiltration. **Recommended.**
- B) Use within-day temporal split (70/30 by timestamp within a single file) — simpler but cross-attack-type generalisation impossible.
- C) Use only synthetic data — already demonstrated; honest but weak for judges.

**Impact on:** R1, R8, R9, R18, R19

---

### Q2. Window Size: 10 Seconds or Larger?

**Context:** `window_size_sec=10.0` is hardcoded. With 10-second windows and CIC-IDS-2018 (recorded at up to 1000 flows/sec), each window may have thousands of flows — large aggregations may lose fine-grained temporal patterns. 

**Options:**
- A) Keep 10 seconds — fast windowing, manageable state vector size. **Reasonable for prototype.**
- B) Use 60 seconds — fewer windows per capture, richer per-window statistics.
- C) Use 5 seconds — more windows, better temporal resolution for fast attacks.

**Impact on:** R6, R11, evaluation granularity

---

### Q3. Which MITRE Stages to Support for Real Data?

**Context:** CIC-IDS-2018 attack types don't map 1:1 to all 5 kill-chain stages. The label-to-stage mapping needs team agreement.

**Proposed mapping (for team approval):**

| CIC-IDS-2018 Label | Stage | Technique |
|---|---|---|
| BENIGN | Benign | — |
| PortScan | Reconnaissance | T1046 |
| FTP-BruteForce, SSH-Bruteforce | Initial Access | T1110 |
| DoS attacks (all types) | Initial Access | T1190 / DoS |
| Bot | Command & Control | T1071 |
| Web Attacks (XSS, SQLi, Brute) | Initial Access | T1190 |
| Infilteration | Exfiltration | T1041 |
| DDOS attack | Reconnaissance (or Initial Access?) | T1498 |

**Questions for team:**
- Should DDoS be classified as Reconnaissance (network mapping) or as a direct attack stage?
- Should lateral movement be included even though CIC-IDS-2018 doesn't have a "Lateral Movement" specific label? (The "Infiltration" label may cover it.)

**Impact on:** R13, stage accuracy evaluation

---

### Q4. Real Packet-Level Features: What to Claim?

**Context:** CIC-IDS-2018 CSVs are flow-level and do NOT contain TTL, IP frag, TCP window, or retransmission counts. The parser fills these with defaults (64, 0, 64240, 0 respectively). The model is trained with these zero-filled values.

**Options:**
- A) **Honestly document the limitation**: "Packet-level features (R4) are available only via PCAP input. CSV input from CIC-IDS-2018 provides flow-level features only." **Recommended — judges respect honesty.**
- B) **Remove packet-level features from FEATURE_COLUMNS**: Drop `ttl_mean`, `ttl_std`, `tcp_window_mean`, `ip_frag_ratio`, `retrans_ratio` from the model input (reduce from 25 to 20 features). Retrain. Cleaner story.
- C) **Include them with a data quality flag**: Keep 25 features but add a binary `packet_features_available` flag. Model learns to weight these features appropriately.

**Impact on:** R4, R5, model performance, judging honesty score

---

### Q5. Model Deployment: Render.com vs Local vs Docker?

**Context:** `render.yaml` deploys to Render.com (cloud). R17 requires fully offline. The submission may be judged on Render but the *claim* of offline must be demonstrable locally.

**Recommended approach:**
- Primary demo: Local `streamlit run app.py` (fully offline after P0-6 font fix)
- Secondary demo: Docker container `docker run -p 8501:8501 sih26153` (air-gapped proof)
- Render deployment: For judges who want to try it without local setup, but clearly label as "cloud convenience deployment, not representative of offline capability"

---

### Q6. Uncertainty Quantification: Monte Carlo Dropout or None?

**Context:** The current model produces deterministic point predictions. Adding MC Dropout (P3-3) would give confidence intervals on the risk trajectory — useful for a SOC analyst.

**Options:**
- A) Skip — too complex for timeline, judges unlikely to penalise absence
- B) Add MC Dropout (P3-3) — 1 day effort, adds epistemic uncertainty bands to forecast chart. **Recommended if time permits.**

---

### Q7. Blockchain Theme: Implement or Not?

**Context:** The hackathon theme includes "Blockchain & Cybersecurity" but the core problem doesn't require it. P3-1 (hash-chained audit log) is a lightweight optional addition.

**Options:**
- A) Implement hash-chained prediction log (P3-1, S effort) — adds theme alignment without complexity
- B) Skip — focus on core requirements

**Recommendation:** Implement P3-1 — it is S-effort (1 day), adds genuine forensic value, and directly addresses the theme without adding cloud dependencies.

---

## Unverifiable Without Full Dataset/GPU

| Question | Why Unverifiable | What Would Resolve It |
|---|---|---|
| Model discrimination on real CIC-IDS-2018 | Need to retrain and evaluate with P0-1,2 fixes | Run `python scripts/train.py` after P0-1,2 |
| Lead time advantage over LR baseline | Depends on real training | Run evaluation after retraining |
| CTU-13 generalisation | Dataset not present | Download CTU-13 scenario CSV |
| Memory usage for 358 MB CSV parse | Not benchmarked | `python -m memory_profiler scripts/train.py` |
| PCAP parse performance for 100 MB PCAP | Not benchmarked | Use `time python -c "from src.parser import TrafficParser; ..."` |
| GradientShap latency with background=200 samples | App not launched in audit | Profile `AttackExplainer.explain_window()` with cProfile |
| Scapy performance on Windows (Npcap required) | No Npcap in audit environment | Install Npcap, test with small PCAP |
