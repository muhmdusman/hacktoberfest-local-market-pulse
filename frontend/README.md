# Local Market Pulse dashboard

A small Next.js dashboard for starting a local-market scan and reviewing customer pain points, competitors, keywords, recommendations, and supporting evidence. It uses local synthetic data by default, so the demo works without the backend.

## Run locally

```bash
npm install
npm run dev
```

Open <http://localhost:3000> and click **Analyze market**. The mock run moves through collection, analysis, trend detection, and report generation before showing the dashboard.

## Mock and live modes

Mocks are enabled by default. You can force them for any visit with:

```text
http://localhost:3000/?mock=1
```

Copy the example environment file when you want explicit local settings:

```bash
cp .env.example .env.local
```

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000/api/v1` | Backend API prefix |
| `NEXT_PUBLIC_USE_MOCKS` | `true` | Use local synthetic payloads instead of HTTP |

To connect the backend, set `NEXT_PUBLIC_USE_MOCKS=false`, update the base URL if needed, and restart `npm run dev`. Public Next.js variables are embedded when the app starts/builds.

## Expected API endpoints

The adapter in `lib/api.ts` is the only frontend integration point. It expects JSON from:

- `GET /options`
- `GET /models`
- `GET /sources/status`
- `POST /runs`
- `GET /runs/{id}`
- `GET /runs/{id}/results`

Each path is appended to `NEXT_PUBLIC_API_BASE_URL`, so the default full prefix is `/api/v1`. Request and response interfaces are in `lib/types.ts`; local demo payloads are in `lib/mock-data.ts`.

## Checks

```bash
npm run lint
npm run build
```
