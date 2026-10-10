<div align="center">

# Local Market Pulse

**Give your AI agent eyes on the internet. Understand what your local market is saying, and grow with it.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-agent-1C3C3C?logo=langchain&logoColor=white)
![LiteLLM](https://img.shields.io/badge/LiteLLM-gateway-4B5563)
![FastAPI](https://img.shields.io/badge/FastAPI-0.143-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Open-weight](https://img.shields.io/badge/Models-open--weight%20%E2%89%A4%208B-6D28D9)

*"The world doesn't run on what gets made. It runs on what gets sold."*

</div>

---

## Overview

Local Market Pulse is an open-source **market-intelligence agent** for small and medium-sized businesses. It lets an AI agent search **Reddit and the open web**, read what people in a specific region say about a product or service category, and turn those conversations into structured, evidence-backed insights:

- the **pain points** customers keep running into
- the **unmet needs**: what customers ask for and can't find
- how **competitors** are perceived, and where they fall short
- what to **follow** (practices customers praise) and what to **avoid** (recurring complaints)
- the **local language** people use when they search, and the **questions** they ask

All reasoning runs on **open-weight models of 8B parameters or fewer**, orchestrated by a **LangGraph** agent and served through a **LiteLLM** gateway.

The insights are a foundation, not an endpoint. They feed our **SEO tool**, and they support business analysis, product and service improvements, and decisions about what to build next.

| | |
|---|---|
| **Domain** | 05 · Business & Productivity (with a Community & Social Good angle) |
| **Approach** | Model harness (LangGraph agent with original routing, validation and escalation logic) + Agent Skill |
| **Core model** | Meta Llama 3.1 8B Instruct (`llama-3.1-8b-instant`) via Groq |
| **Sources** | Reddit and the open web. More platforms are on the roadmap |
| **License** | [MIT](LICENSE) |

## Contents

[Problem](#problem) · [What it does](#what-it-does) · [How the insights are used](#how-the-insights-are-used) · [AI component](#ai-component) · [Architecture](#architecture) · [Original work and building blocks](#original-work-and-building-blocks) · [Tech stack](#tech-stack) · [Getting started](#getting-started) · [API](#api) · [Agent Skill](#agent-skill) · [Testing and findings](#testing-and-findings) · [Project status](#project-status) · [Limitations and responsible use](#limitations-and-responsible-use) · [Roadmap](#roadmap) · [Contributors](#contributors) · [License](#license) · [Acknowledgements](#acknowledgements)

---

## Problem

- **SMEs can't see what their market is saying.** The useful signals are scattered across Reddit threads, forums, review pages and blogs, and nobody has time to read them all.
- **Market-intelligence tools are built for large companies.** Social-listening and SEO-research platforms are priced and designed for enterprise teams.
- **Local conversations are multilingual.** In Pakistan, posts mix English, Urdu script and Roman Urdu ("bohat mehenga hai yaar"), which generic tools handle poorly.
- **So decisions run on guesswork.** Which complaints are common in this area? What are customers missing? Which competitor weaknesses are an opening? Without data, owners guess.

## What it does

```text
business + region + competitors
        │
        ▼
  plan local search queries ──▶ search Reddit and the web ──▶ read posts, comments and pages
        │
        ▼
  understand every post with an open-weight model (≤ 8B) ──▶ validate, repair, escalate
        │
        ▼
  aggregate into trends, gaps and competitor profiles ──▶ structured insights (dashboard + JSON)
```

### What you learn

| Insight | Question it answers | Example (cafés, Islamabad) |
|---|---|---|
| **Pain points** | What problems do customers in this domain keep facing? | Slow Wi-Fi, no backup power during load shedding |
| **Unmet needs** | What do customers ask for that nobody offers? | Late-night seating in F-7, sugar-free options |
| **Competitor landscape** | How is each competitor perceived, and why? | Competitor A praised for coffee, criticised for slow service |
| **Follow** | Which practices do customers consistently praise? | Laptop-friendly seating, clear pricing |
| **Avoid** | What consistently drives complaints? | Hidden service charges, rude staff |
| **Local search language** | Which words and phrases do people use? | "late night cafe F-7", "sasta coffee G-11" |
| **Open questions** | What are people asking that no one has answered well? | "Any cafe open after midnight with good Wi-Fi?" |
| **Emerging trends** | What's being talked about more than before? | Mentions of backup power up sharply in the last 30 days |

Every insight links back to the source posts it came from, so it can be checked.

### Who it's for

- **Product-based businesses**: cafés, restaurants, bakeries, clothing stores, e-commerce shops.
- **Service-based businesses**: clinics, salons, gyms, tutoring centres, repair services, agencies.
- **AI agents**, through the API and the Agent Skill, so an agent can research a market on its own and act on the results.

## How the insights are used

| Use | How Local Market Pulse helps |
|---|---|
| **SEO and content** | Local keywords, real customer questions and content topics go into our SEO tool for keyword targeting, FAQ pages and content plans |
| **Business analysis** | Sentiment by area, recurring themes and competitor benchmarks give a factual view of the local market |
| **Product and service improvement** | Recurring complaints show what to fix first. Praised practices show what to keep |
| **New products and services** | Unmet needs, weighted by how often they come up, point to openings worth building |
| **Competitive strategy** | Competitor strengths and weaknesses show where to differentiate |
| **Customer communication** | Real questions become FAQs, help content and community answers |

## AI component

| Item | Details |
|---|---|
| **Primary model** | Meta **Llama 3.1 8B** Instruct (`llama-3.1-8b-instant`), 8.03B parameters, 8B class |
| **Model license** | Llama 3.1 Community License (open-weight) |
| **Runtime / provider** | Groq cloud API, accessed through **LiteLLM** |
| **Local fallback** | Ollama with Qwen3 1.7B / 4B (Apache-2.0), accessed through the same LiteLLM gateway |
| **Orchestration** | **LangGraph** state graph. Tools and prompts use **LangChain** |
| **Size rule** | The hackathon limit is **≤ 8B parameters**. The model allowlist rejects any larger model (e.g. 14B, 70B) before a call is made |
| **What the model does** | Plans local search queries; classifies relevance and sentiment; extracts pain points, needs, competitor mentions, praise, complaints, keywords and questions as structured JSON; writes the final insight summaries |
| **Why it's central** | Without the model the system only has raw text. Every insight, trend and recommendation comes from model output |

> No proprietary model is used in the product. Proprietary AI assistants were used only as **development tools**, which the event rules allow.

## Architecture

### System architecture

```mermaid
flowchart LR
    subgraph Clients
        UI[Next.js dashboard]
        AGT[External AI agent<br/>via Agent Skill]
        SEO[SEO tool]
    end

    subgraph Backend["FastAPI backend"]
        API[REST API /api/v1]
        subgraph Agent["LangGraph market agent"]
            PLAN[Plan queries]
            COLL[Collect]
            ANA[Analyze]
            SYN[Synthesize insights]
        end
        TOOLS[LangChain tools<br/>Reddit search, web search, page reader]
    end

    subgraph Models["Open-weight models, max 8B"]
        GW[LiteLLM gateway<br/>8B allowlist]
        GROQ[Llama 3.1 8B on Groq]
        OLL[Qwen3 on Ollama<br/>fallback]
    end

    DB[(PostgreSQL)]
    NET[(Reddit and the open web)]

    UI --> API
    AGT --> API
    API --> PLAN --> COLL --> ANA --> SYN
    COLL --> TOOLS --> NET
    PLAN --> GW
    ANA --> GW
    SYN --> GW
    GW --> GROQ
    GW --> OLL
    SYN --> DB
    API <--> DB
    API --> SEO
```

### Agent graph

The LangGraph state graph. The routing, validation and escalation logic is the team's original harness work.

```mermaid
flowchart TD
    S0([Input: business, region, competitors]) --> PQ[plan_queries<br/>LLM expands local search queries]
    PQ --> C1[search_reddit]
    PQ --> C2[search_web]
    C1 --> N[normalize<br/>dedupe, PII scrub, language detection]
    C2 --> N
    N --> R{route}
    R -- off-topic --> DROP[discard]
    R -- plain English --> XS[extract: small tier]
    R -- Urdu, Roman Urdu, code-mixed or long --> XL[extract: large tier]
    XS --> V{validate schema<br/>and confidence}
    XL --> V
    V -- invalid, retries left --> REP[repair with validation error]
    REP --> V
    V -- low confidence on small tier --> XL
    V -- failed after retries --> LOG[log failure]
    V -- valid --> ACC[accept insight]
    ACC --> AGG[aggregate<br/>trends, gaps, competitor profiles]
    AGG --> SYN[synthesize<br/>pain points, unmet needs, follow and avoid, keywords]
    SYN --> S9([Insight report + JSON])
```

### Data flow

```mermaid
flowchart LR
    INP[/Business, region, competitors/] --> P1((Plan and collect))
    NET[(Reddit + open web)] --> P1
    P1 --> P2((Normalize and scrub PII))
    P2 --> D1[(Source records)]
    D1 --> P3((Extract insights))
    P3 <--> GW[LiteLLM gateway to open-weight model]
    P3 --> D2[(Insights + traces)]
    D2 --> P4((Aggregate trends and gaps))
    P4 --> P5((Synthesize findings))
    P5 --> O1[/Dashboard/]
    P5 --> O2[/JSON for agents and the SEO tool/]
    P5 --> O3[/Business and product decisions/]
```

### Request sequence

```mermaid
sequenceDiagram
    actor User as SME or AI agent
    participant API as FastAPI
    participant G as LangGraph agent
    participant T as LangChain tools
    participant L as LiteLLM gateway
    participant M as Open-weight model (max 8B)
    participant DB as PostgreSQL

    User->>API: POST /api/v1/runs (business, region, competitors)
    API->>DB: Create run
    API-->>User: 202 Accepted, run_id
    API->>G: Invoke graph in background
    G->>L: Plan local search queries
    L->>M: Completion request
    M-->>G: Queries
    G->>T: Search Reddit and the web, read pages
    T-->>G: Posts, comments, pages
    loop Each record
        G->>L: Extract structured insight
        L->>M: Completion request
        M-->>G: JSON
        G->>G: Validate, repair or escalate
    end
    G->>G: Aggregate trends and gaps
    G->>L: Synthesize findings
    L->>M: Completion request
    M-->>G: Summary
    G->>DB: Store insights and report
    User->>API: GET /api/v1/runs/{id}/results
    API-->>User: Insights JSON
```

### Data model (planned)

```mermaid
erDiagram
    SCAN_RUN ||--o{ SOURCE_RECORD : collects
    SOURCE_RECORD ||--o| INSIGHT : "analysed into"
    INSIGHT ||--o{ MODEL_ATTEMPT : "traced by"
    SCAN_RUN ||--o{ TREND_ITEM : produces
    SCAN_RUN ||--o| REPORT : summarises

    SCAN_RUN {
        string id PK
        string business
        string region
        string status
        datetime created_at
    }
    SOURCE_RECORD {
        string id PK
        string run_id FK
        string source
        string url
        string text
        string author_hash
        string lang
        datetime posted_at
    }
    INSIGHT {
        string record_id PK
        bool relevant
        string sentiment
        json pain_points
        json unmet_needs
        json praises
        json complaints
        json competitors
        json keywords
        string question
        float confidence
    }
    MODEL_ATTEMPT {
        int id PK
        string record_id FK
        string model
        string tier
        string kind
        bool valid
        int latency_ms
    }
    TREND_ITEM {
        int id PK
        string run_id FK
        string kind
        string term
        int count
        float lift
        float score
    }
    REPORT {
        string run_id PK
        json findings
        string summary
    }
```

## Original work and building blocks

The hackathon's model-harness rules ask teams to say exactly what they implemented. We use established open-source frameworks for plumbing. The decision logic that makes small models reliable on local, multilingual data is ours.

### Built by our team

| Component | What it does | Why it matters |
|---|---|---|
| **Agent graph design** | Node set, shared state and conditional edges in LangGraph: routing by language and confidence, repair loops, escalation paths | Defines how the agent spends model calls and recovers from bad outputs |
| **Language-aware router** | Detects English, Urdu script, Roman Urdu and code-mixed text. Filters off-topic posts. Sends hard posts to the stronger tier | Local Pakistani text is where small models fail most |
| **Structured extraction policy** | Insight schema, validation, repair prompts that include the validation error, confidence thresholds, self-consistency voting | Turns an unreliable small model into a reliable extractor |
| **Model policy** | Allowlist of open-weight models ≤ 8B, enforced before any LiteLLM call | Keeps the system within the rules by construction |
| **Local query planner** | Expands a business and region into local search queries, including area names and Roman Urdu variants | Finds conversations generic search misses |
| **Trend and gap engine** | Recent-vs-baseline lift, z-scores, unmet-need scoring, competitor profiles | Condenses thousands of opinions into a short list of findings |
| **Insight synthesis** | Pain points, unmet needs, follow and avoid lists, local keywords, open questions, all linked to their sources | Output a business can check and act on |
| **Evaluation** | Compares a rule-based baseline, small-only, large-only and routed configurations on labelled posts | Measures what the harness adds |
| **Agent Skill, API and dashboard** | Skill package, FastAPI service with PostgreSQL, Next.js dashboard | Makes the capability usable by people and by agents |

### Open-source building blocks

| Project | Role | License |
|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Graph runtime: state, parallel branches, conditional edges | MIT |
| [LangChain](https://github.com/langchain-ai/langchain) | Tool interface, prompt templates, output parsing | MIT |
| [LiteLLM](https://github.com/BerriAI/litellm) | One API for Groq and Ollama, with retries and fallbacks | MIT |
| [Meta Llama 3.1 8B](https://www.llama.com/) · [Qwen3](https://github.com/QwenLM/Qwen3) | Open-weight models | Llama 3.1 Community · Apache-2.0 |
| FastAPI, SQLAlchemy, PostgreSQL, Next.js | Application stack | MIT · MIT · PostgreSQL · MIT |
| rdt-cli, OpenCLI, Exa, Jina Reader | Reddit and web data access | See each project |

## Tech stack

| Layer | Technology |
|---|---|
| Agent and AI | LangGraph · LangChain · LiteLLM · Llama 3.1 8B (Groq) · Qwen3 (Ollama fallback) |
| Backend | Python 3.12 · FastAPI 0.143 · Pydantic Settings · SQLAlchemy 2.1 (async) · asyncpg · Uvicorn |
| Database | PostgreSQL 16 (Docker) |
| Frontend | Next.js 16 · React 19 · Tailwind CSS 4 · TypeScript |
| Data access | Reddit search and read · web search · Jina Reader for public pages |
| Testing | pytest · pytest-asyncio · httpx · live curl checks |
| Tooling | uv · Docker Compose · npm |

### Project structure

```text
hacktoberfest-local-market-pulse/
├── backend/                       FastAPI service
│   ├── app/
│   │   ├── api/                   routers and dependencies
│   │   ├── core/                  settings (reads ../.env.local)
│   │   ├── db/                    async engine, session, models
│   │   ├── schemas/               request and response models
│   │   └── services/              business logic
│   ├── tests/                     unit, database and live curl tests
│   └── pyproject.toml
├── frontend/                      Next.js dashboard
├── docker/
│   └── docker-compose.local.yml   PostgreSQL for local development
├── docs/                          context, plan, UI and API contract
├── .env.example                   copy to .env.local
├── rules-hackathon.md
└── LICENSE                        MIT
```

## Getting started

### Prerequisites

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- Docker with Docker Compose
- Node.js 20+ and npm
- A Groq API key, or a local Ollama install

### 1. Configure the environment

```bash
cp .env.example .env.local    # .env.local is git-ignored. Never commit real keys
```

| Variable | Purpose |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT` | Postgres container settings |
| `DATABASE_URL` | Async SQLAlchemy URL, e.g. `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `DB_ECHO` | Log SQL statements (`true` / `false`) |
| `APP_NAME`, `APP_ENV`, `API_V1_PREFIX` | API metadata and route prefix (default `/api/v1`) |
| `GROQ_API_KEY` | Groq key read by LiteLLM *(added with the agent)* |
| `LLM_MODEL_SMALL`, `LLM_MODEL_LARGE` | LiteLLM model ids, e.g. `groq/llama-3.1-8b-instant` *(added with the agent)* |
| `OLLAMA_API_BASE` | Local Ollama endpoint for the fallback, e.g. `http://localhost:11434` *(added with the agent)* |

### 2. Start PostgreSQL

```bash
docker compose --env-file .env.local -f docker/docker-compose.local.yml up -d
```

### 3. Run the backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

- API docs: <http://127.0.0.1:8000/docs>
- Liveness: <http://127.0.0.1:8000/api/v1/health>
- Database readiness: <http://127.0.0.1:8000/api/v1/health/db>

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

### 5. Run the tests

```bash
cd backend
uv run pytest                  # unit and database tests (Postgres must be running)
uv run pytest -m live          # live curl checks against a running server
```

## API

All routes are served under `API_V1_PREFIX` (default `/api/v1`). Interactive documentation is at `/docs`.

| Method | Endpoint | Description | Status |
|---|---|---|---|
| `GET` | `/api/v1/health` | Liveness probe (no database access) | Implemented |
| `GET` | `/api/v1/health/db` | Readiness probe. Returns `503` when Postgres is down | Implemented |
| `GET` | `/api/v1/models` | Allowed models, active tiers, 8B rule | Planned |
| `GET` | `/api/v1/sources/status` | Which data sources are reachable | Planned |
| `POST` | `/api/v1/runs` | Start a market scan (runs the agent in the background) | Planned |
| `GET` | `/api/v1/runs/{id}` | Scan status and progress | Planned |
| `GET` | `/api/v1/runs/{id}/results` | Pain points, unmet needs, competitors, follow and avoid, keywords, questions, trends | Planned |
| `GET` | `/api/v1/runs/{id}/posts` | Analysed source posts, with filters | Planned |
| `GET` | `/api/v1/runs/{id}/posts/{record_id}` | One post, its insight and the agent's trace | Planned |
| `GET` | `/api/v1/runs/{id}/export` | Full results as JSON, for agents and the SEO tool | Planned |

Request and response shapes: [docs/UI_AND_API.md](docs/UI_AND_API.md).

> The API has **no authentication** and is meant to run locally. Add authentication before exposing it on a network.

## Agent Skill

`skills/local-market-pulse/` packages the capability as an [Agent Skill](https://agentskills.io/specification), so any compatible AI agent can run a market scan and use the results.

- `SKILL.md`: when to use the skill, step-by-step instructions, a worked example, edge cases
- `scripts/`: entry point that starts a scan and returns the insights as JSON
- `references/`: insight schema and data-source notes

Example request an agent can handle: *"What are customers in Islamabad complaining about when it comes to gyms, and what are they missing?"*

## Testing and findings

| # | Scenario | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| 1 | Liveness probe | `GET /api/v1/health` | `200 {"status":"ok"}` | _to record_ | Pending |
| 2 | Database readiness, Postgres up | `GET /api/v1/health/db` | `200 {"status":"ok","database":"up"}` | _to record_ | Pending |
| 3 | Database readiness, Postgres down | Broken session stub | `503 {"status":"error","database":"down"}` | _to record_ | Pending |
| 4 | Oversized model rejected | Request a 70B model | Rejected before any call | _to record_ | Pending |
| 5 | Roman Urdu routing | "yaar ye cafe bohat mehenga hai" | Routed to the large tier | _to record_ | Pending |
| 6 | Invalid JSON repair | Model returns broken JSON once | Valid insight after one repair | _to record_ | Pending |
| 7 | PII scrubbing | Post containing `0300-1234567` | Phone number replaced with `[phone]` | _to record_ | Pending |
| 8 | End-to-end scan | Cafés, Islamabad | Results with every insight type populated | _to record_ | Pending |

Evaluation results (baseline vs small-only vs large-only vs routed) will be added after the labelled run.

## Project status

| Component | Status |
|---|---|
| Backend foundation: FastAPI, settings, async database session, health and readiness endpoints, tests | Done |
| PostgreSQL via Docker Compose | Done |
| Frontend scaffold (Next.js, Tailwind) | Done |
| LangGraph agent: query planning, collection, routing, extraction, synthesis | In progress |
| LiteLLM gateway with the 8B model allowlist | In progress |
| Reddit and web tools | In progress |
| Trend and gap engine | In progress |
| Dashboard screens | In progress |
| Agent Skill | In progress |
| Evaluation | In progress |

## Limitations and responsible use

- **Two sources for now.** Only Reddit and the public web. More platforms are on the roadmap.
- **Small samples are noisy.** With little data, trend scores are signals, not proof.
- **Reddit access** depends on a session the user already has. The system never automates logins or reads browser cookies.
- **Privacy.** Usernames are hashed (SHA-256), and emails and phone numbers are removed before any text reaches a model.
- **Read-only.** The agent observes and reports. It never posts, comments or messages on any platform.
- **Evidence over invention.** Every insight links to its source posts. Where a business fact is needed, such as an FAQ answer, the system leaves a draft for the owner.
- **Demo data.** Any synthetic demo dataset is labelled as such and uses fictional business names.

## Roadmap

- More sources: review platforms, Facebook groups, YouTube comments, X
- Direct integration with our SEO tool (Search Console analysis to actionable issues)
- Scheduled scans with change alerts ("complaints about delivery doubled this month")
- Multi-region comparison
- Larger hand-labelled evaluation set for Urdu and Roman Urdu

## Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/razi-ur-rehman"><img src="https://github.com/razi-ur-rehman.png" width="90" alt="razi-ur-rehman"/><br/><b>razi-ur-rehman</b></a><br/>
      <sub><i>Contribution: to be added</i></sub>
    </td>
    <td align="center">
      <a href="https://github.com/Muhaddis-igis"><img src="https://github.com/Muhaddis-igis.png" width="90" alt="Muhaddis-igis"/><br/><b>Muhaddis-igis</b></a><br/>
      <sub>Backend and database: FastAPI, PostgreSQL, Docker, tests</sub>
    </td>
    <td align="center">
      <a href="https://github.com/muhmdusman"><img src="https://github.com/muhmdusman.png" width="90" alt="muhmdusman"/><br/><b>muhmdusman</b></a><br/>
      <sub>Product, documentation and frontend</sub>
    </td>
  </tr>
</table>

Contributions are welcome through issues and pull requests. Never commit secrets: `.env.local` is git-ignored.

## License

Released under the [MIT License](LICENSE). Copyright © 2026 Muhammad Usman and contributors.

You may use, copy, modify and distribute this project as long as the license and copyright notice are kept. Third-party frameworks and models remain under their own licenses, listed in [Open-source building blocks](#open-source-building-blocks).

## Acknowledgements

- [LangGraph](https://github.com/langchain-ai/langgraph), [LangChain](https://github.com/langchain-ai/langchain) and [LiteLLM](https://github.com/BerriAI/litellm)
- [Meta Llama 3.1](https://www.llama.com/) and [Qwen3](https://github.com/QwenLM/Qwen3)
- [Groq](https://groq.com/) and [Ollama](https://ollama.com/)
- [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/), [PostgreSQL](https://www.postgresql.org/), [Next.js](https://nextjs.org/), [Tailwind CSS](https://tailwindcss.com/)
- [rdt-cli](https://github.com/public-clis/rdt-cli), [OpenCLI](https://github.com/jackwener/opencli), [Exa](https://exa.ai/) and [Jina Reader](https://github.com/jina-ai/reader)
- [Agent-Reach](https://github.com/Panniantong/Agent-Reach) (MIT), reference for multi-platform data access
- [Agent Skills specification](https://agentskills.io/specification)
- Hacktoberfest Islamabad 2026, organised by CNCF Islamabad and powered by MLH

---

<div align="center">
<sub>Built in Islamabad for Hacktoberfest 2026.</sub>
</div>
