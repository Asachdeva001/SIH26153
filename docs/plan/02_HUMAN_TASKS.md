# SIH 26153 — Human-Only Tasks

These items **cannot or must not be delegated to the coding agent**. Some require real-world access (billing, an email address, a camera), some require credentials the agent should never generate or hold, and some are product/strategy decisions the team needs to own. The agent's task list (`01_AGENT_TASKS.md`) references these by ID and will pause/flag rather than attempt them itself.

Work through these **in parallel with the agent's Phase 0–3 work** so Phase 4 (cloud training) isn't sitting idle waiting on you.

---

## H0. Confirm no backup of the deleted `src/` exists anywhere (blocks Agent Task 0.1)
- **What:** before the agent spends time on git-history archaeology, quickly check the places an agent typically can't: a teammate's local clone that was never pushed, a shared Drive/zip backup, a different branch/fork, Slack/Discord file shares, or an old CI artifact. Also confirm whether anyone has the original `world_model_v1.pth`/`scaler.pkl` sitting on a laptop — that alone would save the reconstruction from starting fully untrained.
- **Why it must be human:** the agent can only search the repo it has access to; it can't message teammates or check personal drives/laptops.
- **Output needed by agent:** either the recovered files (best case), or an explicit "confirmed gone" so it proceeds straight to `00b_SRC_RECONSTRUCTION_SPEC.md` (Task 0.1, Step B) without wasting time.

---

## H — Cloud Account & Access (blocks Agent Phase 4)

### H1. Choose AWS or GCP
- **What:** Pick a primary cloud provider for training + (optionally) hosting.
- **Why it must be human:** it's a cost/team-familiarity/timeline decision, not a technical one the agent can weigh for you.
- **Output needed by agent:** which provider, so it writes `s3://...` or `gs://...` paths consistently.
- **Notes from audit:** `13` recommends AWS `g4dn.xlarge` (~$0.52/hr on-demand, ~$0.15/hr spot) or GCP `n1-standard-4` + T4 (~$0.40/hr spot). Model is small (~64k params), so a single mid-tier GPU is enough — don't over-provision.

### H2. Create the cloud account and enable billing
- **What:** AWS or GCP account, billing method attached, **a budget alert configured** (audit `13` §9 recommends an alert around $20/month for this project's scale — adjust to your comfort level).
- **Why it must be human:** requires a payment method and legal account ownership.

### H3. Create scoped IAM credentials (not root/owner keys)
- **What:** an IAM user or service account with **read-write access limited to the specific S3/GCS bucket(s)** used by this project — not admin/root credentials.
- **Why it must be human:** issuing credentials is an access-control decision with real security consequences; the agent should never create or hold account-owner-level keys.
- **Output needed by agent:** an access key ID/secret (AWS) or a service-account JSON key (GCP), delivered to the agent **only as an environment variable / secrets file that is gitignored**, never pasted into a committed file or into chat history that gets saved to the repo.
- **Related agent task:** 4.1, 4.2 (agent writes the code to *use* these credentials via env vars; it does not generate them).

### H4. Provision the training VM/instance
- **What:** launch the actual EC2/GCE instance (or SageMaker/Vertex AI training job) once Task 4.2's script is ready to be dry-run for real.
- **Why it must be human:** requires account access and incurs real cost; also a good checkpoint to sanity-check the instance size/spend before committing.
- **Output needed by agent:** SSH access or a remote-execution method (e.g., AWS SSM Session Manager, `gcloud compute ssh`) so it can run `train_cloud.sh` and report results, or you run the script yourself and hand the agent the resulting logs/metrics to interpret.

### H5. Request GPU quota increase (if needed)
- **What:** AWS/GCP often cap GPU instance quota at 0 for new accounts; you may need to file a support request.
- **Why it must be human:** tied to account identity verification, sometimes requires a support ticket with a business justification.
- **Timing:** do this early (Day 1) — quota approval can take hours to days.

### H6. Confirm the training VM shuts down after the run
- **What:** after Task 4.3's real training run, manually confirm (via the AWS/GCP console) that the instance actually terminated/stopped, not just that the script *attempted* to shut it down.
- **Why it must be human:** the agent's Task 4.5 only tests the shutdown logic locally/in dry-run; someone needs to eyeball the console to prevent surprise billing.

---

## D — Dataset Access

### D1. Obtain/confirm access to the full CIC-IDS-2018 (or chosen) dataset
- **What:** the audit found only a single 358MB day-file (`02-14-2018.csv`) was used previously, sourced from a Kaggle mirror. Decide: stick with the single-day subset, or pull the full 10-day dataset from the official source (CIC's own hosting) for more convincing generalisation results.
- **Why it must be human:** may require creating a Kaggle account/API token, agreeing to dataset terms of use, or requesting access from the official CIC portal — an account/legal-terms action.
- **Output needed by agent:** either the dataset files placed in the agreed local/S3 location, or credentials (Kaggle API token) delivered the same secure, gitignored way as H3.

### D2. Decide which dataset(s) back the final submitted results
- **What:** single-day CSV vs. multi-day vs. adding CTU-13/UNSW-NB15 for cross-dataset generalisation testing (per Agent Task 2.3).
- **Why it must be human:** a scope/time-tradeoff decision affecting both training cost (H1/H4) and the strength of the R9 (generalisation) claim in judging.

---

## S — Strategic / Product Decisions

### S1. AWS vs. GCP (see H1) — same decision, listed here for visibility in planning docs.

### S2. Live cloud demo vs. fully local/offline demo on judging day
- **What:** the audit (`13` §10, `12`) explicitly recommends running the judging-day demo **fully local/offline** (`docker-compose up` on a laptop with the pre-downloaded trained weights), showing the cloud pipeline logs/CI as *proof* of production-readiness rather than depending on a live cloud connection during judging.
- **Why it must be human:** this is a risk-tolerance and pitch-strategy call for the team, not something the agent can decide. It also directly affects how R17 (offline) is framed in front of judges.
- **Recommendation from audit:** go local/offline for the live demo; show cloud artifacts as evidence.
- **Action:** make the call explicitly and tell the agent, so Task 6.4's rehearsal is built around the right mode.

### S3. License choice (MIT vs. Apache-2.0 vs. other)
- **What:** Agent Task 3.6 will default to MIT if you don't specify — confirm this is acceptable, or state your preference.

### S4. Label-to-risk severity mapping sign-off
- **What:** Agent Task 1.5 will propose a `LABEL_TO_RISK` mapping (e.g., BENIGN=0.05, Bot=0.85, FTP-BruteForce=0.60, etc.). This is a modeling judgment call with real evaluation consequences — review the proposed mapping before it's baked into the training run in Phase 2/4.
- **Why it must be human:** it encodes a domain judgment (how severe is each attack type) that should reflect real security reasoning, not just whatever the agent guesses; a judge may also ask you to justify these numbers.

### S5. MITRE ATT&CK stage-mapping review
- **What:** review whichever mapping logic the agent restores/rewrites for `RuleBasedMITREMapper` (rules or thresholds mapping predicted future states to Reconnaissance/Initial Access/Lateral Movement/C2/Exfiltration) for domain correctness before the demo.
- **Why it must be human:** requires security domain knowledge to sanity-check against MITRE's actual technique definitions; also worth having the mapping table ready to defend if judges probe it.

---

## R — Recording & Submission Deliverables

### R1. Record the 2-minute demo video
- **What:** actually record, per the script drafted in Agent Task 6.3/`10`, the screen capture + narration.
- **Why it must be human:** requires a camera/screen-recorder, a human voice, and editing — not something the agent can produce. The agent can prepare the script and rehearse the click-through (Task 6.4) but cannot record or narrate it.
- **Depends on:** Agent Task 6.4 (final rehearsal) being green first, and H6/D2/S2 decisions being finalized so the demo reflects the real submitted state.

### R2. Finalize and design the 5-slide deck
- **What:** take the agent's outline + speaker notes (Task 6.3) and turn it into an actual polished slide deck (PowerPoint/Google Slides/Canva).
- **Why it must be human:** visual design and presentation polish; the agent can draft content, not final design assets.

### R3. Upload source code and confirm the public/judge-accessible link
- **What:** push the final repo state, confirm the GitHub link is public (or shared correctly) per R22, and confirm large files (datasets, weights) are excluded via `.gitignore`/Git LFS as appropriate rather than bloating the repo.
- **Why it must be human:** repo visibility/sharing settings are an account-level action.

### R4. Final submission package assembly
- **What:** gather source link, README, architecture doc, demo video link, and slides into whatever format/portal SIH requires, and submit before the deadline.
- **Why it must be human:** submission portals require human identity/account actions and a final human sign-off that everything is accurate before it goes in.

---

## Quick Reference: What NOT to Ask the Agent to Do

- Create or fund a cloud account, or generate root/owner-level credentials.
- Decide AWS vs GCP, or live-demo vs local-demo, on its own.
- Sign up for dataset access requiring an account/terms agreement.
- Record, narrate, or edit the demo video.
- Design the final slide deck visuals.
- Make the final judgment call on the label-severity mapping or ATT&CK stage-mapping without your review.
- Submit anything to the SIH portal.

Everything else in `01_AGENT_TASKS.md` is fair game for the agent, provided the human prerequisites in this file are delivered to it (credentials via secure env vars, dataset location, and the S2/S3/S4/S5 decisions) at the right point in the timeline shown in `00_IMPLEMENTATION_PLAN.md` §6.
