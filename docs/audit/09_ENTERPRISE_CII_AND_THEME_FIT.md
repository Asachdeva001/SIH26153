# SIH26153 — Enterprise, CII & Theme Fit Audit

**Audit Date:** 2026-09-21

---

## Enterprise/CII Applicability Assessment (R20)

### What Is Demonstrated

| Feature | Present | Evidence | Quality |
|---|---|---|---|
| Air-gapped / offline inference | ⚠️ Partial | All ML is local. One CDN dependency (Google Fonts) breaks strict offline | Remove CDN → fully offline |
| On-prem deployment | ✅ | Docker container (`Dockerfile`) runs on any Linux server | Good |
| Asset criticality tiers | ✅ | `AssetCriticalityManager` (world_model.py:272-293): Tier 1/2/3 classification | Good for demo |
| SOC workflow integration | ✅ | Playbooks with SLA response times (P1 < 15 min) | Good narrative |
| SIEM export | ⚠️ | JSON download only (app.py:920-928) — not CEF, STIX, or syslog format | Needs improvement |
| IP anonymisation | ❌ | IPs are aggregated as counts in state vector (good for model), but raw IPs shown in Topology tab (app.py:885) without anonymisation option | |
| OT/ICS traffic support | ❌ | No Modbus, DNP3, or ICS protocol awareness | |
| CICIoT2023 support | ❌ | Not referenced; column aliases not defined | |
| Multi-sensor aggregation | ❌ | Single-source input only | |
| Streaming/online inference | ❌ | Batch processing only; entire file loaded at once | |
| High-throughput link support | ❌ | PCAP path loads entire file into RAM via Scapy | |
| Privacy (no payload storage) | ✅ | Payload bytes are aggregated to mean per window; raw payload not stored | |

### CII Positioning Narrative

The system is positioned for:
1. **Enterprise SOC dashboards** — the 8-tab UI, asset criticality tiers, and playbook automation are well-suited for a Tier-2/3 SOC analyst workstation
2. **Government intranet monitoring** — the "National Cyber Defense Operations" branding and NTRO framing are contextually appropriate
3. **Post-incident forensic analysis** — the JSON audit report export and network topology inspector support incident triage

**Gaps for production CII deployment:**
- No STIX/TAXII threat intelligence export (CII operators need standard formats)
- No alert de-duplication / suppression logic
- No edge deployment mode (the system currently processes complete captures, not streaming flows)
- No integration with real SIEM (Splunk, QRadar, Elastic SIEM) via webhooks or CEF syslog

---

## Threat Model Coverage

| Kill-Chain Stage | Covered? | Evidence |
|---|---|---|
| Reconnaissance (port scan, host discovery) | ✅ | Rule: `port_scan_score > 3.0` and SYN probe pattern |
| Initial Access (brute force, exploit) | ✅ | Rule: `syn_ratio > 0.3` AND `bytes_pkt > 300` |
| Execution / Installation | ❌ | Not modelled — requires endpoint data |
| Persistence | ❌ | Not modelled |
| Privilege Escalation | ❌ | Not modelled |
| Lateral Movement | ✅ | Rule: `unique_dsts ≥ 3` AND `high_port_ratio > 0.4` |
| Command & Control | ✅ | Rule: low IAT variance (beaconing signature) |
| Collection | ❌ | Not modelled |
| Exfiltration | ✅ | Rule: high `total_bytes` and `bytes_per_packet_mean` |
| Impact (ransomware, wiper) | ❌ | Not modelled |

**Out of scope (honestly):** Host-based indicators (file system, registry, process), DNS exfiltration, encrypted C2 (HTTPS), living-off-the-land techniques. The scope limitation should be stated in the submission.

---

## Blockchain & Cybersecurity Theme (R20 — Theme Note)

The problem does NOT require blockchain. The project does not implement blockchain. Below are **recommended optional enhancements** that would:
- Align with the hackathon theme (Blockchain & Cybersecurity)
- Add genuine value to enterprise/CII applicability
- Remain fully offline-safe

### Enhancement Options (Ranked: Value vs Effort)

| Enhancement | Value | Effort | Offline-Safe? | Description |
|---|---|---|---|---|
| **Hash-chained prediction audit log** | ⭐⭐⭐ High | S (1-2 days) | ✅ Yes | Each SOC alert/prediction gets a SHA-256 hash chained to the previous (blockchain-lite). Tamper-evident log for forensic integrity. Store in SQLite or append-only log file. |
| **Signed model artifact** | ⭐⭐ Medium | S (1 day) | ✅ Yes | Hash the model weights at training time; store hash in a JSON manifest. On load, verify hash. Prevents tampered model substitution. |
| **IPFS-based threat indicator sharing** | ⭐ Low | L (5-7 days) | ❌ Requires network | Share STIX threat indicators via IPFS for inter-agency sharing. Too complex for hackathon timeline. |
| **Merkle-tree evidence log** | ⭐⭐ Medium | M (2-3 days) | ✅ Yes | Merkle tree of all prediction events within a session — any tampering invalidates the root hash. Good for court-admissible forensic evidence. |

### Recommended Implementation: Hash-Chained Prediction Audit Log

This adds maximum theme alignment with minimum disruption:

```python
# In the audit report exporter (app.py Tab 8):
import hashlib, json

def chain_prediction(previous_hash: str, prediction_event: dict) -> tuple[str, dict]:
    event_json = json.dumps(prediction_event, sort_keys=True)
    current_hash = hashlib.sha256(
        (previous_hash + event_json).encode()
    ).hexdigest()
    return current_hash, {
        "previous_hash": previous_hash,
        "hash": current_hash,
        "event": prediction_event
    }
```

This produces a tamper-evident chain of every prediction event — if any entry is modified, all subsequent hashes become invalid. Fully offline, adds genuine cybersecurity forensic value, and directly demonstrates the Blockchain theme.
