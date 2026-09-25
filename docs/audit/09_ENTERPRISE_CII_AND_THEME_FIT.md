# SIH26153 — Enterprise, CII & Theme Fit Audit (v2)

**Audit Date:** 2026-09-23

## Changelog — Re-audit (frontend/backend split + cloud training)
- **Deployment Topology:** Evaluated the new split-stack (FastAPI + Next.js) for Enterprise/CII suitability.
- **Air-Gapping:** Added guidelines for deploying the cloud-trained model in a restricted SOC network.

---

## 1. Enterprise/CII Applicability Assessment (R20)

### What Is Demonstrated

| Feature | Present | Status (v2) | Notes |
|---|---|---|---|
| Split-Tier Architecture | ✅ | Excellent | Modern SOC apps decouple frontend logic from heavy ML inference. The Next.js + FastAPI split mimics standard enterprise patterns. |
| Air-gapped deployment | ⚠️ Partial | Missing Docker | The code itself is offline-capable (no external CDNs), but the lack of Dockerfiles means deploying it to an air-gapped machine currently requires manually installing Python, Bun, Node, and building locally. |
| Asset criticality tiers | ❌ Broken | Model deleted | `AssetCriticalityManager` was in the deleted `src/world_model.py`. The API (`backend/routers/soc.py`) fails on import. |
| SOC workflow integration | ✅ UI Only | API broken | Playbook UI is clean, but backend logic is missing. |

### The "Cloud vs. Air-Gapped" Positioning Conflict
The team plans to train the model on AWS/GCP (which is correct and scalable), but they must be careful about **where inference runs**. 
Critical Information Infrastructure (CII) operators (e.g., NTRO, power grids) do not stream raw PCAPs to a public Vercel/Render cloud URL for inference due to data classification rules. 

**Recommendation for SIH Pitch:**
Position the cloud architecture strictly as the **Training Control Plane**. State clearly in the presentation: *"We leverage AWS for scalable training on petabytes of traffic, but the FastAPI + Next.js inference bundle is deployed entirely on-premise inside the SOC's air-gapped network."*

---

## 2. Threat Model Coverage

Because the ML code was deleted, no threat models are currently covered. 
*(See previous v1 audit report for the historical coverage of Reconnaissance, Initial Access, Lateral Movement, C2, and Exfiltration).*

---

## 3. Blockchain & Cybersecurity Theme (R20)

As noted in the original audit, the problem does not inherently require blockchain. The previous recommendation remains the highest-value addition if time permits:

### Hash-Chained Prediction Audit Log (Tamper-Evident Forensics)
Instead of streaming logs to a cloud SIEM, the FastAPI backend should write each prediction event to a local append-only JSONL file, chaining the SHA-256 hash of the previous event. 
If an insider threat tampers with the SOC risk scores in the database, the chain breaks. This perfectly aligns with the Blockchain theme while maintaining 100% offline capability.
