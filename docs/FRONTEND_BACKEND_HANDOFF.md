# Frontend ↔ Backend Handoff (Current Implementation)

Use this as the live integration contract for the Next.js dashboard in `frontend/`.

## Run locally

```powershell
# Terminal 1 — repository root
docker compose --env-file .env.local -f docker/docker-compose.local.yml up -d --wait

# Terminal 2 — backend/
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 3 — frontend/
npm run dev
```

Frontend `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_USE_MOCKS=false
```

Open <http://localhost:3000>. API docs: <http://127.0.0.1:8000/docs>.

## Implemented pipeline

```text
POST /runs
  → LangGraph planner agent (ALLAM 2 7B on Groq)
  → LangGraph ToolNode executes web_search / reddit_search
  → collector deduplicates and balances Reddit + web hits
  → evaluator agent classifies each hit into validated Insight JSON
  → invalid JSON gets up to two repair attempts
  → strategist aggregates pain points, requests, keywords and competitors
  → strategist model writes three actions
  → scan, result rows, Insight JSON and trace metrics are saved in PostgreSQL
  → GET /runs/{id}/results returns the dashboard report
```

Reddit currently uses privacy-safe web discovery (`site:reddit.com` via DDGS); it does not authenticate, read cookies, or post. This is the no-credential fallback inspired by Agent-Reach's ordered-backend capability pattern. A later collector can put authenticated `rdt-cli` ahead of DDGS without changing the graph.

## Frontend endpoints

All paths below are relative to `/api/v1`.

| Method | Path | Dashboard use |
|---|---|---|
| GET | `/options` | Form choices and limits |
| GET | `/models` | Active open-weight model and enforced ≤8B gate |
| GET | `/sources/status` | Current collector backend badges |
| POST | `/runs` | Start a scan; returns `202 {run_id,status}` |
| GET | `/runs/{id}` | Poll stage/progress until `done` or `failed` |
| GET | `/runs/{id}/results` | Full typed report for all dashboard sections |
| GET | `/runs/{id}/report.md` | Downloadable Markdown report |
| GET | `/runs/{id}/report.html` | Downloadable standalone HTML report |

The old `/scans` endpoints remain as internal/debug endpoints. The frontend should only use `/runs`.

## Stages exposed to the UI

Internal graph stages are translated to the frontend's fixed enum:

- planner/search/collector → `collecting`
- evaluator → `analyzing`
- strategist aggregation → `trending`
- database/report finalization → `reporting`
- complete → `done`

## Current model and eligibility

The configured Groq account no longer exposes Llama 3.1 8B to its developer tier. It does expose `allam-2-7b`, which is an Apache-2.0, open-weight 7B model and passes the code-enforced 8.5B exact ceiling for the event's 8B class rule. The registry rejects GPT-OSS 20B/120B, Qwen 27B and Llama 70B before a provider call.

ALLAM lacks native Groq tool calling. To preserve real tool use, the planner emits a validated JSON tool plan; the backend converts it to standard LangChain `tool_calls`; LangGraph `ToolNode` executes those calls. This is visible in logs and saved query data.

## Important frontend behavior

- Poll every 1 second after `POST /runs`.
- Fetch `/results` only once status is `done`; it returns `409` while running.
- Render backend strings with React text nodes; do not inject HTML.
- `mode`, `urls`, `provider`, and `votes` are accepted for contract compatibility. The first delivered feature runs live DDGS search and the configured Groq model. Cached snapshots, URL ingestion, tier routing, Kev routing and self-consistency are follow-up sprints.
- CORS permits local Next.js origins on ports 3000/3001.

## First core feature status

Verified end to end with a real Islamabad café run: six model-planned searches, 15 deduplicated web/Reddit results, all 15 evaluated by ALLAM 2 7B, 14 marked relevant, summaries/actions persisted to PostgreSQL, and results fetched from the API. This is the working evaluation/demo path.
