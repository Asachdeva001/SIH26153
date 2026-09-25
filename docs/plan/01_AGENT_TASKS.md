# SIH 26153 — Agent Task List

**Give this whole file to your coding agent.** It is an ordered, numbered checklist derived from `docs/audit/00`–`13`. Work through tasks **in order within each phase**; phases must complete in order (Phase 1 cannot start until Phase 0's verification passes, etc.) unless a task explicitly says it can run in parallel.

---

## MANDATORY VERIFICATION PROTOCOL — RUN THIS AFTER *EVERY* TASK

Do not mark any task complete, and do not move to the next task, until all of the following pass. If any step fails, fix it before proceeding — do not skip ahead.

1. **Backend boots clean:**
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```
   - No `ModuleNotFoundError` / `ImportError` on startup.
   - `GET http://localhost:8000/docs` returns 200 and renders the OpenAPI UI.
   - `GET http://localhost:8000/healthz` (or the equivalent health route — create one in Task 0.5 if missing) returns 200 and confirms the model/forecaster is loaded (not `None`).
2. **Frontend boots clean:**
   ```bash
   cd frontend
   bun install
   bun run dev
   ```
   - No build/runtime errors in the terminal.
   - `http://localhost:3000` loads the dashboard with no red console errors in the browser dev tools.
3. **Frontend build (production) still succeeds:**
   ```bash
   bun run build
   ```
4. **End-to-end smoke test** — exercise the real pipeline, not just the UI shell:
   - Upload a small real or synthetic CSV/PCAP fixture through the UI (or via `curl`/`httpx` directly against the API if the UI isn't wired yet).
   - Confirm `/api/upload` returns 200 with windows/raw_packets, not a 500.
   - Confirm `/api/forecast` returns a risk trajectory of the expected length K.
   - Confirm `/api/mitre` returns a stage.
   - Confirm `/api/xai` returns attributions.
   - Confirm `/api/benchmark` returns a comparison payload.
   - Record the exact commands/requests used and their responses (success or failure) in `docs/audit/verification-log.md`, appending one dated entry per task (see format below).
5. **Regression check:** re-run `pytest` (once tests exist from Phase 3 onward) and confirm no previously-passing test now fails.
6. **Log the result.** Append to `docs/audit/verification-log.md`:
   ```
   ## Task <ID> — <title> — <date>
   Backend boot: PASS/FAIL (details)
   Frontend boot: PASS/FAIL (details)
   Frontend build: PASS/FAIL (details)
   E2E smoke test: PASS/FAIL (details, include which endpoints were hit and their status codes)
   Tests: PASS/FAIL/N-A
   Notes: <anything relevant, e.g. "healthz not yet implemented, verified via /docs instead">
   ```

If a task cannot be verified this way (e.g., a cloud-only task with no local equivalent), say so explicitly in the log and state what alternative check was used instead.

---

## PHASE 0 — RECOVERY (blocks everything else)

### Task 0.1 — Attempt git restore first, then reconstruct `src/` from the contract spec if restore fails
- **Why:** `01`, `02`, `04`: backend crashes with `ModuleNotFoundError: No module named 'src'`.
- **Step A (try restore, but don't lose time on it):**
  ```bash
  git log --all --diff-filter=D --summary | grep -i "src/"
  git log --all --oneline -- src/
  ```
  If a commit containing `src/` is found in the full history (`--all`, including other branches, stashes via `git fsck --unreachable`, and any reflog entries), restore it: `git checkout <commit> -- src/`. Confirm the restored files aren't empty stubs before trusting them.
- **Step B — if Step A finds nothing (confirmed by the human that no backup/branch/zip exists either — see `HUMAN_TASKS.md` note below): reconstruct `src/` from `00b_SRC_RECONSTRUCTION_SPEC.md`.** That spec was assembled from the audit reports' documented API contracts, schemas, feature lists, and the exact model architecture (layer shapes, loss function) that were recorded *before* the deletion — so this is not a guess, it's rebuilding a known interface. Follow it module by module:
  1. `src/parser.py` — `TrafficParser` (CSV + PCAP paths, feature extraction, windowing)
  2. `src/synthetic_generator.py` — `SyntheticAttackGenerator`
  3. `src/world_model.py` — `PyTorchTransitionLSTM`, `WorldModelForecaster`, `AssetCriticalityManager`
  4. `src/mitre_mapper.py` — `RuleBasedMITREMapper`
  5. `src/explainer.py` — `AttackExplainer`
  6. `src/evaluator.py` — the corrected `evaluate_k_horizons` logic (build this one correctly from day one — do not reintroduce the self-comparison bug described in Phase 1, Task 1.6)
- **Important:** because there are no original weights to restore either, any model loaded after this task will be **freshly initialized/untrained** until Phase 2. Do not treat a successful import as "the model works" — it will produce random output until trained. Note this explicitly in the verification log.
- **Acceptance criteria:** `src/` directory exists with all modules listed above; `python -c "import src.world_model, src.parser, src.explainer, src.mitre_mapper, src.evaluator, src.synthetic_generator"` succeeds with no import errors; every function/class signature matches what `backend/routers/*.py` and `backend/schemas/requests.py` actually call/expect (verify this explicitly, function by function — a name or argument mismatch here will cause the exact same crash you're fixing).
- **Verify:** run the full protocol above. Since there's no trained model yet, the "non-degenerate predictions" checks later in this phase should instead confirm "runs without error and returns correctly-shaped output" — flag prediction *quality* checks as N/A until Phase 2.

### Task 0.2 — Wire `src/` into the backend correctly
- **Why:** confirm the restored code is actually importable from `backend/` (packaging/path issue), not just present on disk.
- **How:** check `backend/models/loader.py` imports; ensure `pip install -e ..` or an equivalent `PYTHONPATH`/package structure is documented and works from a clean shell.
- **Acceptance criteria:** `uvicorn backend.main:app` starts without falling back to a `None` forecaster.
- **Verify:** run the full protocol above.

### Task 0.3 — Confirm frontend↔backend wiring still matches
- **Why:** `02`, `06`: confirm the API contract (`lib/types.ts` vs `backend/schemas/requests.py`) hasn't silently drifted while `src/` was missing.
- **How:** compare each Pydantic response model to its corresponding TypeScript interface field-by-field; fix mismatches.
- **Acceptance criteria:** no TypeScript errors from mismatched API shapes when the frontend renders real (non-mocked) API responses.
- **Verify:** run the full protocol above, paying attention to each of the 8 dashboard tabs individually.

### Task 0.4 — Add a `/healthz` endpoint if missing
- **Why:** needed by the verification protocol itself, and by any future container orchestrator (ECS/Cloud Run) readiness/liveness probes.
- **How:** add a `GET /healthz` route that checks the forecaster/model object is loaded and returns `{"status": "ok", "model_loaded": true}` or a 503 if not.
- **Acceptance criteria:** endpoint exists and returns correctly in both the "model loaded" and (temporarily, for testing) "model missing" cases.
- **Verify:** run the full protocol above.

### Task 0.5 — Create `docs/audit/verification-log.md`
- **Why:** every subsequent task needs somewhere to log its verification run.
- **How:** initialize the file with a short header explaining its purpose, then log Task 0.1–0.4's results into it now (retroactively, one entry each).
- **Acceptance criteria:** file exists with at least 5 entries (0.1–0.5).

---

## PHASE 1 — CORRECTNESS & SECURITY FIXES

### Task 1.1 — Fix event-loop-blocking upload route
- **Why:** `01`, `03`, `08`: `async def upload_file` runs `shutil.copyfileobj` and `parser.parse_csv` synchronously, freezing the whole server during any upload.
- **How:** either change the route to plain `def` (FastAPI auto-threadpools it) or explicitly wrap the blocking calls with `await anyio.to_thread.run_sync(...)`. Apply the same review to every other route — confirm `forecast.py` (already `def`, per `04`) and check `xai.py`, `mitre.py`, `benchmark.py`, `report.py`, `scenario.py`, `soc.py` for the same anti-pattern.
- **Acceptance criteria:** no `async def` route performs blocking file I/O or CPU-bound parsing/inference directly on the event loop. Prove it by uploading a large (~100MB+) file and confirming a concurrent lightweight request (e.g., `/healthz`) still responds quickly instead of hanging.
- **Verify:** run the full protocol above, including a concurrency test (fire the health check while a large upload is in flight).

### Task 1.2 — Fix path traversal in upload handler
- **Why:** `01`, `08`, `10`: `os.path.join("scratch", file.filename)` allows `../../etc/passwd`-style paths.
- **How:** sanitize with `os.path.basename(file.filename)` at minimum; better, generate a server-side random/UUID filename and store the original name separately if needed for display.
- **Acceptance criteria:** an upload with a filename like `../../evil.csv` is safely contained inside the intended scratch directory (write a quick manual/automated test proving this).
- **Verify:** run the full protocol above.

### Task 1.3 — Lock down CORS
- **Why:** `08`: `allow_origins=["*"]` in `main.py`.
- **How:** read the frontend origin from an environment variable (e.g., `FRONTEND_URL`, default `http://localhost:3000` for dev) and pass it as the CORS allow-list instead of `*`.
- **Acceptance criteria:** CORS config is environment-driven; wildcard is gone.
- **Verify:** run the full protocol above, confirming the frontend at `localhost:3000` can still call the backend successfully with the new config.

### Task 1.4 — Add upload size limit
- **Why:** `08`, `12`: no `Content-Length` check; a huge file can OOM the container.
- **How:** enforce a max size (start with 500MB, make it configurable via env var) by checking `Content-Length` up front and/or streaming with a cap, returning `413 Payload Too Large` past the limit.
- **Acceptance criteria:** an oversized synthetic file (or a mocked large `Content-Length` header) is rejected with a clear error instead of crashing or hanging.
- **Verify:** run the full protocol above.

### Task 1.5 — Fix the label-engineering bug (real data → all-zero risk)
- **Why:** `03`, `10` (P1-1): the CIC-IDS `Label` column (BENIGN/Bot/FTP-BruteForce/etc.) was never mapped to the model's expected `target_risk_score` (0.0–1.0), so training on real data silently produced all-zero targets.
- **How:** implement a `LABEL_TO_RISK` mapping (or a more principled severity scale) covering every label value present in the dataset actually being used; apply it before training; fail loudly (raise, don't silently zero-fill) if a `KeyError`/unmapped label is encountered.
- **Acceptance criteria:** running the mapping over the real CIC-IDS-2018 CSV produces a target column with a real distribution of values (not all zeros) — print/assert the value counts as proof.
- **Verify:** run the full protocol above (this doesn't require a full training run yet — that's Phase 2 — just confirm the mapping function itself is correct and covers all observed label values).

### Task 1.6 — Fix the self-comparison evaluation bug
- **Why:** `05`: `gt_binary = (wm_preds > 0.40).astype(int)` derives "ground truth" from the model's own predictions, guaranteeing meaningless F1 scores (observed: WM F1=0.000 vs baseline F1=0.982 — an artifact of the bug, not a real result).
- **How:** rewrite the benchmark/evaluation logic to compare predictions at horizon `t+k` against the **actual future label** at `t+k` from the held-out set, not against the model's own current-step output. Implement the `evaluate_k_horizons` function sketched in `05` (or an improved version) producing `F1@1..F1@K`, precision, recall, and FPR per horizon.
- **Acceptance criteria:** the evaluation function, run on a small synthetic or real test set, produces different, plausible F1 values that are NOT a trivial function of the model's own output threshold; add a unit test that would fail against the old buggy implementation.
- **Verify:** run the full protocol above, plus the new unit test.

### Task 1.7 — Fix train/test split for realistic evaluation
- **Why:** `10` (P1-2): grouped/temporal split logic collapses when only a single CSV file is present.
- **How:** implement a temporal split (e.g., by timestamp quantile — first 70% chronologically = train, next 15% = val, last 15% = test) that works correctly for both single-file and multi-file inputs.
- **Acceptance criteria:** `len(train_df) > 0`, `len(val_df) > 0`, `len(test_df) > 0` for a single-file input, with no row-level leakage across splits (assert no duplicate timestamps/flow IDs across split boundaries).
- **Verify:** run the full protocol above.

---

## PHASE 2 — REAL LOCAL TRAINING & HONEST EVALUATION

*(All tasks in this phase must build on the fixes from Phase 1 — do not train before Task 1.5–1.7 are done, or you will bake the same bugs into the model.)*

### Task 2.1 — Run a local training pass on real CIC-IDS-2018 data (subset OK)
- **Why:** `04`: the previously committed weights were trained **only on synthetic data**; the model has never seen real traffic. If Task 0.1 went through Step B (reconstruction), there are **no prior weights at all** — this is now training from scratch, not fine-tuning, so treat any prior audit language about "the existing model" as no longer applicable.
- **How:** using the fixed label mapping and split logic, run `scripts/train.py` (reconstructed/repaired per `00b_SRC_RECONSTRUCTION_SPEC.md`) on the real dataset file(s) available locally (a single day's CSV is fine for this local pass — full multi-day training happens in Phase 4 on the cloud). Also run a quick sanity pass on purely synthetic data first (`SyntheticAttackGenerator`) to confirm the training loop itself is mechanically correct (loss decreases, shapes match) before spending time on the real dataset — this isolates "is the code right" from "is real data harder."
- **Acceptance criteria:** training completes without error; loss decreases over epochs (log and save the curve); resulting `.pth`/scaler are saved locally.
- **Verify:** run the full protocol above, plus load the new weights into the backend and confirm `/api/forecast` returns non-degenerate (not constant, not NaN) predictions on a held-out sample.

### Task 2.2 — Run the fixed K-horizon evaluation and record honest metrics
- **Why:** produce a real, defensible F1@1..F1@K / precision / recall / FPR table, replacing the fabricated F1=0.000 result.
- **How:** run the Task 1.6 evaluation function against the model from Task 2.1 on the held-out test split; also run the logistic-regression baseline on the **same** features/split for a fair comparison.
- **Acceptance criteria:** save `benchmark_report.json` with real numbers; the world model and baseline numbers must not be identical or trivially derived from each other; write one sentence in the report honestly stating whether the world model beats the baseline or not, and by how much.
- **Verify:** run the full protocol above, plus confirm `/api/benchmark` now serves these real numbers to the frontend and the Benchmark tab renders them correctly.

### Task 2.3 — Sanity-check generalisation
- **Why:** `04` (R9): confirm the model isn't just memorizing.
- **How:** if a second dataset file/day is available locally, evaluate the Task 2.1 model on it without retraining; otherwise, hold out one entire attack type from training and test purely on that type.
- **Acceptance criteria:** results (however good or bad) are recorded honestly in `docs/audit/verification-log.md` and in the evaluation report; do not discard bad results — report them.
- **Verify:** run the full protocol above.

---

## PHASE 3 — PACKAGING, TESTS, CI (parallelizable with late Phase 2)

### Task 3.1 — Write backend Dockerfile
- **Why:** `01`, `08`, `10` (P0-5): Dockerfiles were deleted; no reproducible deployment artifact exists.
- **How:** multi-stage Dockerfile: build stage installs Python deps (including any native deps for Scapy/libpcap), final stage is slim, runs as non-root user, exposes 8000, does **not** bake in model weights (loaded at runtime per Phase 4's handoff design).
- **Acceptance criteria:** `docker build -t sih-backend ./backend` succeeds; `docker run -p 8000:8000 sih-backend` boots and passes the `/healthz` check.
- **Verify:** run the full protocol above using the Docker container instead of the local `uvicorn` process for the backend leg.

### Task 3.2 — Write frontend Dockerfile
- **Why:** same as above, for Next.js/Bun.
- **How:** multi-stage: `bun install` + `bun run build` in build stage, slim runtime stage running `bun run start` (or Next.js standalone output), exposes 3000.
- **Acceptance criteria:** `docker build -t sih-frontend ./frontend` succeeds; container serves the dashboard on port 3000.
- **Verify:** run the full protocol above using the Docker container for the frontend leg.

### Task 3.3 — Write `docker-compose.yml`
- **Why:** local air-gapped demo target (per `13`, §10) needs a single-command full-stack run.
- **How:** compose file wiring backend (port 8000) + frontend (port 3000, `NEXT_PUBLIC_API_URL` pointed at the backend service), plus a named volume or bind mount for the model artifacts directory.
- **Acceptance criteria:** `docker-compose up` brings up both services; the dashboard at `localhost:3000` successfully calls the backend at `localhost:8000` with CORS correctly configured per Task 1.3.
- **Verify:** run the full protocol above end-to-end via `docker-compose up`, including the full upload→forecast→mitre→xai→benchmark→soc smoke test.

### Task 3.4 — Restore/write automated tests
- **Why:** `01`, `08`, `10` (P1-6): zero test coverage currently.
- **How:** add `pytest` unit tests for: `src/parser.py` (feature extraction correctness on a small fixture CSV/PCAP), `src/world_model.py` (forward pass shape/sanity, the Task 1.6 evaluation logic), and `httpx`/FastAPI `TestClient` integration tests for every route in `backend/routers/` (happy path + at least one error path each, e.g., malformed upload, empty file, path-traversal filename).
- **Acceptance criteria:** `pytest` passes locally; every route in `backend/routers/` has at least one test; the Task 1.6 regression test (bad-eval-logic detector) is included.
- **Verify:** run the full protocol above, with the "Tests" line in the log now reporting real pass/fail counts instead of N/A.

### Task 3.5 — Set up GitHub Actions CI (lint/test/build only — no deploy/cloud credentials)
- **Why:** `08`, `10` (P1-5); CI must not require cloud secrets to run on every PR.
- **How:** `.github/workflows/lint-and-test.yml` running `ruff`/`flake8` + `mypy` (optional) + `pytest` for the backend, and `eslint` + `bun run build` for the frontend, on every push/PR. Do **not** include the cloud-deploy or cloud-training workflow in this task — that requires human-provisioned credentials (see `HUMAN_TASKS.md`) and belongs to Phase 4/5.
- **Acceptance criteria:** workflow file exists and is green on a test PR/push.
- **Verify:** run the full protocol above locally to confirm the same commands the CI will run actually pass.

### Task 3.6 — Add `LICENSE` file
- **Why:** `01` (R21): open-source license required, currently missing.
- **How:** add an MIT or Apache-2.0 `LICENSE` file at repo root (confirm with the team which one — default to MIT if no preference is given, and note the assumption in the verification log).
- **Acceptance criteria:** `LICENSE` file present at repo root.
- **Verify:** log the file's presence in `docs/audit/verification-log.md` (no runtime verification needed for this one).

---

## PHASE 4 — CLOUD TRAINING PIPELINE

> **Blocked on human action:** this phase needs a cloud account, billing alert, and IAM credentials that only a human can create (see `HUMAN_TASKS.md`, items H1–H3). Do not attempt to create an AWS/GCP account, enable billing, or generate root credentials yourself. Once the human provides you with (a) a bucket name, (b) an IAM user/service-account key with scoped S3/GCS read-write access only, and (c) a target instance type, proceed with the tasks below.

### Task 4.1 — Parameterize data/model I/O for object storage
- **Why:** `04`, `13`: training script currently hardcodes local paths.
- **How:** add `fsspec`/`s3fs` (AWS) or `gcsfs` (GCP) support so `train.py`/`train_cloud.py` can read `s3://bucket/raw/...` or `gs://bucket/raw/...` as easily as a local path, and write checkpoints/final artifacts back the same way. Keep local-path support working too (for Phase 2's local runs and the CI tests).
- **Acceptance criteria:** the same training script runs correctly against a local path (regression check) and, once credentials are supplied by the human, against the cloud bucket path.
- **Verify:** run the full protocol above for the local-path case; log the cloud-path case separately once credentials exist (see H2 in `HUMAN_TASKS.md`).

### Task 4.2 — Write `train_cloud.sh` / `train_cloud.py`
- **Why:** `04`, `10` (P0-4), `13`: reproducible one-command cloud training run.
- **How:** script that (1) pulls code + data from the bucket, (2) installs dependencies, (3) runs training with the Phase 1/2 fixes applied, (4) runs the Task 1.6/2.2 evaluation, (5) uploads `world_model_v1.pth`, `scaler.pkl`, `metrics.json`/`benchmark_report.json` to `s3://.../releases/<timestamp>-<git-commit-hash>/`, and (6) writes/updates a `manifest.json` (or `latest` pointer) referencing the newest release.
- **Acceptance criteria:** script is idempotent and fully parameterized (no hardcoded bucket names/paths — use env vars); dry-run it locally against a local "fake bucket" (a plain directory) to prove the logic before it ever touches real cloud credentials.
- **Verify:** run the full protocol above using the local dry-run mode.

### Task 4.3 — Execute the cloud training run
- **Why:** produce the real, full-dataset-trained model.
- **How:** once the human has provisioned the VM/instance and handed over access (see `HUMAN_TASKS.md` H4), SSH in (or use the provided remote-execution method) and run `train_cloud.sh` for real.
- **Acceptance criteria:** training completes; artifacts land in the bucket under a timestamped release folder; `metrics.json` shows real, non-degenerate, non-self-referential numbers consistent with Task 2.2's local sanity check.
- **Verify:** log the full run (commands, duration, final metrics) in `docs/audit/verification-log.md`. This task's "frontend/backend boot" verification is: pull the resulting artifact down locally and repeat Task 2.1's local verification (load into backend, confirm non-degenerate predictions) before declaring this task done.

### Task 4.4 — Implement model handoff (backend pulls "latest" release at startup)
- **Why:** `13`, §5: don't bake large binaries into the Docker image; support easy model updates.
- **How:** in the backend's startup lifecycle, read `MODEL_VERSION` (or default to "latest") from env, download the corresponding `.pth`/`scaler.pkl` from the bucket (or from a local models directory if `MODEL_SOURCE=local`, for the offline demo build) into a local cache dir, then load as before.
- **Acceptance criteria:** backend can start in both modes (`MODEL_SOURCE=local` for the air-gapped demo, `MODEL_SOURCE=s3` for a connected environment) and loads correctly in each.
- **Verify:** run the full protocol above in `local` mode (mandatory) and, if credentials are available, in `s3` mode as well (log separately).

### Task 4.5 — Auto-shutdown / cost guardrail script for the training VM
- **Why:** `13`, §9: avoid idle GPU billing.
- **How:** add a final step to `train_cloud.sh` (or a wrapping systemd unit/cron) that shuts the instance down after artifacts are confirmed uploaded.
- **Acceptance criteria:** script includes the shutdown step; test the upload-confirmation check logic locally (without actually shutting anything down) by mocking the "upload succeeded" condition.
- **Verify:** code review + local dry-run log entry; actual instance shutdown behavior can only be confirmed by the human during the real run (Task 4.3).

---

## PHASE 5 — PRODUCTION HARDENING

### Task 5.1 — Convert upload to job/status pattern (or SSE/WebSocket streaming)
- **Why:** `07`, `10` (P2-1), `12`: large uploads currently block the HTTP request until fully parsed, risking ALB/Cloud Run/Nginx `504` timeouts, and give the user no progress feedback.
- **How:** implement `POST /api/upload` returning a `job_id` immediately (using FastAPI `BackgroundTasks` or a simple in-memory/queue-backed job store), plus `GET /api/upload/status/{job_id}` for polling. Update the Next.js client to poll and show a progress indicator instead of a blocking spinner.
- **Acceptance criteria:** uploading a large file returns immediately with a `job_id`; the frontend shows progressive status; the final result is retrievable once the job completes.
- **Verify:** run the full protocol above, including a large-file timing test showing the initial response is fast regardless of file size.

### Task 5.2 — Client-side file validation
- **Why:** `07`: no size/type check before hitting the backend.
- **How:** in the upload component, reject files over the configured limit and non-CSV/PCAP types before the request is sent, with a clear inline error message.
- **Acceptance criteria:** oversized/wrong-type files are rejected client-side with a visible message; the backend limit from Task 1.4 remains as defense-in-depth.
- **Verify:** run the full protocol above.

### Task 5.3 — Replace hand-written frontend types with generated OpenAPI types
- **Why:** `06`, `08`: `lib/types.ts` is hand-maintained and can silently drift from the Pydantic schemas.
- **How:** add an `openapi-typescript` (or equivalent) generation step (npm/bun script) that pulls `backend`'s `/openapi.json` and generates types into `frontend/src/lib/generated/`; replace manual interfaces with the generated ones where practical.
- **Acceptance criteria:** generation script runs successfully against the live backend; frontend builds using the generated types with no type errors.
- **Verify:** run the full protocol above.

### Task 5.4 — Rate limiting on expensive endpoints
- **Why:** `06`, `08`: `/api/xai` (Captum GradientShap) is CPU-intensive; concurrent hits can lock up a small container.
- **How:** add `slowapi` (or equivalent) rate limiting to `/api/xai` and any other CPU-heavy route; make limits configurable via env var.
- **Acceptance criteria:** hitting the endpoint beyond the configured rate returns `429` instead of degrading the whole service.
- **Verify:** run the full protocol above, plus a simple burst test against the limited endpoint.

### Task 5.5 — Secrets via environment/secret manager, never committed
- **Why:** `08`, `13`: Kaggle API keys and any future cloud secrets must not live in `.env` files committed to git.
- **How:** confirm `.gitignore` excludes all `.env*` files; document (in README) that in production these are injected via AWS Secrets Manager/SSM Parameter Store or GCP Secret Manager, not files — actual secret provisioning is a human task (see `HUMAN_TASKS.md`).
- **Acceptance criteria:** `git grep` for anything resembling an API key/secret in the current tree and history returns nothing; `.env.example` documents every required variable with placeholder values only.
- **Verify:** log the `git grep`/history-scan results in `docs/audit/verification-log.md`.

### Task 5.6 — Structured logging
- **Why:** production observability.
- **How:** add structured (JSON) logging with request id, route, latency, and model version on each prediction request; explicitly avoid logging raw uploaded payloads or full IPs/PII beyond what's needed.
- **Acceptance criteria:** logs are structured and inspectable; a sample log line is included in the PR/commit description.
- **Verify:** run the full protocol above and inspect actual log output during the E2E smoke test.

---

## PHASE 6 — DELIVERABLES SCAFFOLDING (final content/recording is human work — see `HUMAN_TASKS.md`)

### Task 6.1 — Rewrite `README.md`
- **Why:** `01` (R23): current README has no working setup instructions for the new architecture.
- **How:** cover: problem framing, architecture diagram (reuse/adapt the Mermaid diagrams from `docs/audit/02`), prerequisites, exact clean-clone setup commands for backend + frontend + docker-compose, how to run tests, how to run local training, how to run cloud training (pointing to `HUMAN_TASKS.md` for the credential-provisioning steps), known limitations (be honest about anything still unresolved), and the benchmark results table from Task 2.2/4.3.
- **Acceptance criteria:** every command in the README has been actually run and confirmed to work during this task's verification.
- **Verify:** run the full protocol above by literally following the new README from a clean checkout.

### Task 6.2 — Write the 2-page architecture document
- **Why:** `13` deliverable R24.
- **How:** produce a concise doc (Markdown, convertible to PDF) covering system architecture, data flow, world-model design, ATT&CK mapping approach, and the cloud training/serving split, using diagrams already produced in the audit reports as a base — update any that reference deleted/now-restored code.
- **Acceptance criteria:** document is ≤2 pages when rendered to PDF; technically accurate against the current, verified codebase (not the pre-restructure or pre-fix state).
- **Verify:** log completion; no runtime verification applicable, but cross-check every claim in the doc against actual code/tests from earlier phases.

### Task 6.3 — Draft the 5-slide outline and speaker notes
- **Why:** `13` deliverable R26.
- **How:** use the outline from `10` (updated demo script) as a base: (1) problem & why static IDS fails, (2) world-model architecture, (3) features & data (flow+packet), (4) results vs. baseline incl. generalisation, (5) demo/CII applicability/roadmap. Draft speaker notes per slide.
- **Acceptance criteria:** outline + notes document exists; every number/claim in it traces back to a real, verified result from Phase 2/4.
- **Verify:** log completion.

### Task 6.4 — Final full-stack rehearsal (local, offline, `docker-compose`)
- **Why:** this is the actual judging-day demo path per `13`, §10.
- **How:** with cloud-trained weights downloaded locally (human-provided per `HUMAN_TASKS.md`), run `docker-compose up` with networking otherwise unrestricted but no calls actually made to any external service, and walk through the entire upload→forecast→mitre→xai→benchmark→soc flow exactly as the demo video/live demo will.
- **Acceptance criteria:** a full run-through completes with no errors, no visible loading-state failures, and no unexpected network calls (verify via browser dev tools Network tab — every request should go to `localhost:8000`, none to external hosts).
- **Verify:** run the full protocol above one final time; this is the log entry that should be referenced as "release-ready" in the final summary.

---

## FINAL STEP — SUMMARY REPORT

After Task 6.4, produce a short summary (append to `docs/audit/verification-log.md` or a new `docs/audit/FINAL_STATUS.md`):
- Which tasks are done vs. still open.
- The final, honest benchmark numbers (world model vs. baseline, per horizon).
- Any item that could not be completed because it depends on a human task that wasn't finished yet — list it explicitly, do not silently drop it.
- Updated Readiness Score estimate (re-run the same 7-area scoring rubric from `docs/audit/00_EXECUTIVE_SUMMARY.md`).

**Do not implement anything beyond this task list without checking back in.** If you discover a new blocker not covered here, add it to `docs/audit/12_OPEN_QUESTIONS.md` and flag it rather than silently improvising a fix outside this plan's scope.
