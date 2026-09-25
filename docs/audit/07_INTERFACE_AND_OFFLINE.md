# SIH26153 — Interface & Offline Audit (v2)

**Audit Date:** 2026-09-23

## Changelog — Re-audit (frontend/backend split + cloud training)
- **Architecture Shift:** The interface is now a Next.js (App Router) application managed by Bun.
- **Offline Definition:** R17 is clarified: the cloud training pipeline is permissible; the offline requirement applies strictly to the inference/demo payload.

---

## 1. Interface Identification

The interface is a **Next.js (App Router) web application** located in `frontend/src/app/`.
- Written in TypeScript and React 19.
- Uses Tailwind CSS and Recharts.
- Clear separation of concerns into components (`ControlPanel`, `MetricCard`, `ForecastTimeline`, etc.).
- The dashboard page (`dashboard/page.tsx`) orchestrates state across 8 tabs.

This is a massive improvement in code quality and scalability over the monolithic Streamlit app.

---

## 2. Offline Audit (R17) Re-Evaluation

The prompt clarifies R17: *Training on an AWS/GCP VM does not violate R17 as long as the deployed inference/demo path has no dependency on third-party cloud APIs at request time.*

**Frontend Network Analysis (`bun run build` output):**
| Asset/Network Call | Status | Impact on Air-Gapped Deployment |
|---|---|---|
| Google Fonts | ✅ Localized | `next/font/google` (`Inter`) is configured in `layout.tsx`. Next.js downloads Google Fonts at **build time** and serves them locally. |
| Vercel Analytics | ✅ None | No tracking scripts found. |
| CDN Scripts | ✅ None | Recharts and Tailwind are bundled into the static payload. |
| Backend API | ✅ Configurable | `lib/api.ts` uses `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'`. Fully self-hostable. |

**Verdict on R17 (Inference):** ✅ **PASS.** The Next.js + FastAPI deployment contains zero runtime third-party network calls. It is genuinely air-gap capable for CII enterprise deployments.

---

## 3. Fake-Demo Detector Results

| Red Flag | Found? | Location | Severity |
|---|---|---|---|
| Hard-coded/demo data | ✅ FOUND | `fetchScenario()` in `lib/api.ts` requests a synthetic scenario by default | 🟠 Expected fallback, but must be disclosed |
| Fake benchmark values | ❌ FIXED | The hardcoded `3.5` was removed. `frontend/src/app/components/tabs/Benchmark.tsx` correctly reads `lead_time_advantage` from the API. | 🟢 |
| Buttons that do nothing | ⚠️ Partial | SOC playbooks still only render UI badges. | 🟡 Acceptable for demo |

---

## 4. Large-File Upload UX & API Contract

File upload is handled in `frontend/src/app/dashboard/page.tsx` and `lib/api.ts`:
```typescript
const res = await fetch(`${API_BASE_URL}/upload`, {
  method: 'POST',
  body: formData
});
```

**Production UX Flaws:**
1. **No Progress Bar:** `uploadFile()` is a synchronous `await` without XMLHttpRequest progress events. If a user uploads a 1GB PCAP, the UI will freeze on the Spinner for minutes with no feedback.
2. **Synchronous Backend:** As noted in the Data audit, FastAPI processes the file synchronously on the event loop. This will cause Nginx/AWS ALB to return a `504 Gateway Timeout` for large files.
3. **No File Validation:** The frontend does not check if `file.size > LIMIT` or `file.type == pcap/csv` before sending it to the backend.

**Recommended Fix (Cloud Ready):** 
1. FastAPI should return a `job_id` immediately.
2. Next.js should poll `/api/upload/status/{job_id}` and show a progress bar.
3. Add client-side size validation to `ControlPanel.tsx`.

---

## 5. UI/UX Error States

| Scenario | Handled? | Location |
|---|---|---|
| Backend Unreachable | ✅ Partial | `try/catch` in `loadBaseData` throws `alert("Error loading data. Check backend connection.")`. Needs a better UI toast. |
| Upload API Error | ❌ No | Rejects promise, triggers generic alert. |
| Empty File | ❌ No | Passes through to backend, backend crashes. |
| Loading States | ✅ Yes | `<Spinner />` overlay during `isXaiLoading` and `isLoading`. |
| Responsiveness | ✅ Yes | Tailwind `grid-cols-1 md:grid-cols-2 xl:grid-cols-4` handles mobile/tablet breakpoints cleanly. |
