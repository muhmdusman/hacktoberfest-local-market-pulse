# UI & API Contract — Local Market Pulse

This is the agreement between the **dashboard** (`frontend/`) and the **backend** (`pulse/api/`). Build both sides against it so neither waits on the other. If you need to change a field, change this file first and tell the team.

Related: [CONTEXT.md](CONTEXT.md) · [PLAN.md](PLAN.md)

## 1. UI goals

- **Easy for a non-technical shop owner:** plain words ("Find opportunities", not "Run pipeline"), one form, one button, results in tabs.
- **Shows the AI at work for judges:** every post can be opened to show which model and tier handled it, repairs, escalation and the extracted JSON.
- **Works offline at the venue:** "Quick demo" mode uses the cached snapshot and model cache. No CDN files at runtime; any library is vendored into `frontend/vendor/`.
- **Accessible basics:** a `<label>` on every input, keyboard-navigable tabs, sentiment shown as text + colour (never colour alone), WCAG AA contrast. Full WCAG compliance would need manual testing with assistive tech; we only claim these basics.

## 2. Stack (fixed)

| Part | Choice | Why |
|---|---|---|
| Backend API | **FastAPI** + **uvicorn** (pin exact versions) | Small, typed, auto docs at `/docs` |
| Frontend | **Static HTML + vanilla JS + CSS** in `frontend/`, served by FastAPI at `/` | No build step, no Node needed at the venue |
| Charts | Plain CSS bar charts (div widths) | No dependency, works offline |
| Dev without backend | `frontend/mock/*.json` fixtures, open `/?mock=1` | Frontend dev can start right away |

Run: `.venv/bin/pulse serve` → <http://127.0.0.1:8000> (UI) and <http://127.0.0.1:8000/docs> (API docs).

## 3. Screens

### Screen 1: New scan (home)

| Element | Type | Maps to API field |
|---|---|---|
| "What's your business?" | Select: Café, Restaurant, Gym, Salon, Other (+ text box) | `business` |
| "City" | Text, default **Islamabad** | `city` |
| "Areas (optional)" | Chips: F-6, F-7, F-8, F-10, F-11, G-9, G-11, E-7, Blue Area, DHA, Bahria | `areas[]` |
| "Competitors (optional)" | Comma-separated text | `competitors[]` |
| "Where should we listen?" | Checkboxes: Reddit ☑, Web ☑ | `sources[]` |
| "Extra web pages (optional)" | Textarea, one URL per line, max 10 | `urls[]` |
| Mode | Radio: **Quick demo (saved data)** / Live search | `mode`: `cached` / `live` |
| Source status strip | Small badges, e.g. "Reddit: using Exa (rdt not installed)" | `GET /api/sources/status` |
| Model badge | e.g. "AI: Llama 3.1 8B via Groq · ≤8B ✓" | `GET /api/models` |
| **Find opportunities** | Primary button | `POST /api/runs` |
| "Open last report" | Link | `GET /api/runs` (first item) |

Validation in the UI: business required, at least one source, URLs must start with `http(s)://`. The backend validates again.

### Screen 2: Progress

- Stepper: **Collect → Understand (AI) → Find trends → Write report** (`stage`).
- Progress bar for the AI step: `progress.done / progress.total`.
- Live counters: posts collected, kept, filtered, escalated to the large model.
- Messages list: fallbacks and warnings from collectors (`messages[]`).
- Poll `GET /api/runs/{id}` every 1 s. When `status = done`, go to Screen 3. On `failed`, show `error.message` with a "Try quick demo" button.

### Screen 3: Results dashboard (tabs)

| Tab | What's shown | Data |
|---|---|---|
| **Overview** | KPI cards (posts analysed, relevant %, sentiment split bar, top rising topic, escalation rate). "Top 3 actions this week" list. Provenance banner (SYNTHETIC DEMO DATA / MockProvider when applicable) | `results.overview`, `results.provenance` |
| **Keywords** | Table: phrase, mentions, trend badge (↑ rising when lift > 1.5), score, example post. "Copy all" button | `results.keywords` |
| **Customer voice** | Pain points bar chart, requests bar chart, real questions list | `results.voice` |
| **Competitors** | Table: name, mentions, sentiment split bar, negativity %, top complaints. Gap list: "Nobody serves: late-night hours (gap 7.2)" | `results.competitors`, `results.gaps` |
| **Content plan** | Brief cards (title, target keyword, outline, weakness addressed, "Copy as Markdown"). FAQ list + "Copy FAQ schema (JSON-LD)" | `results.content` |
| **Reddit threads** | List: title, subreddit, age, the question, "Open on Reddit". Honest-participation note always visible. *(Stretch)* "Draft a helpful reply" → model draft the user copies and posts **manually** | `results.threads`, `POST .../draft-reply` |
| **Posts explorer** | Filterable table (source, language, tier, escalated, sentiment, search). Row → drawer showing scrubbed text, extracted Insight JSON, model, tier, repairs, escalated, latency | `GET .../posts`, `GET .../posts/{record_id}` |
| Downloads | "Download report (HTML)", "Download report (Markdown)" | `GET .../report.html`, `GET .../report.md` |

### Screen 4: Under the hood (AI & harness)

- Models table: id, provider, size class, exact params, license, tier, "≤8B ✓" badge. A note that the registry rejects anything larger (e.g. 70B).
- Harness metrics for the selected run: calls per tier, cache hits, escalation rate, repairs, schema-failure rate, p50/p95 latency, tokens.
- Routing diagram (static image or a Mermaid render exported to SVG).
- Eval table (baseline vs small-only vs large-only vs routed) and a "Run evaluation" button.

## 4. API conventions

- Base path `/api`, JSON in and out, UTF-8 (Urdu text must round-trip).
- Times are ISO-8601 UTC strings. Scores are floats rounded to 2 decimals.
- Errors always look like `{"error": {"code": "not_found", "message": "Run abc123 not found"}}` with codes 400, 404, 409, 422 (validation) and 500.
- Run artifacts live in `out/runs/<run_id>/` (`run.json`, `records.jsonl`, `insights.jsonl`, `metrics.json`, `results.json`, `report.md`, `report.html`).
- The run id **`demo`** is always available: it's pre-built from the cached snapshot at startup, or on the first request.
- **Security:** binds to `127.0.0.1` by default and has **no authentication** (it's a local single-user tool). Put auth in front before exposing it on a network. User-supplied URLs pass a public-URL check (http/https only, no private/loopback IPs, adapted from Agent-Reach `utils/url.py`). Limits: ≤10 URLs, `limit` ≤200. API keys are never returned in any response. The frontend renders all text with `textContent`, never `innerHTML`.

## 5. Endpoints

| # | Method & path | Purpose | Priority |
|---|---|---|---|
| 1 | `GET /api/health` | Liveness | P0 |
| 2 | `GET /api/options` | Form defaults (business types, areas, default competitors) | P0 |
| 3 | `GET /api/models` | Registry + active tiers + 8B rule | P0 |
| 4 | `GET /api/sources/status` | Which collector backends work right now | P1 |
| 5 | `POST /api/runs` | Start a scan (background job) | P0 |
| 6 | `GET /api/runs` | List recent runs | P1 |
| 7 | `GET /api/runs/{run_id}` | Status + progress (polled) | P0 |
| 8 | `GET /api/runs/{run_id}/results` | Everything for the dashboard tabs in one payload | P0 |
| 9 | `GET /api/runs/{run_id}/posts` | Paginated, filterable analysed posts | P1 |
| 10 | `GET /api/runs/{run_id}/posts/{record_id}` | One post + insight + harness trace | P1 |
| 11 | `GET /api/runs/{run_id}/report.md` · `/report.html` | Download the report | P0 |
| 12 | `POST /api/eval` · `GET /api/eval/latest` | Run / fetch the eval comparison | P2 |
| 13 | `POST /api/runs/{run_id}/threads/{record_id}/draft-reply` | Model-drafted helpful reply (human posts it) | Stretch |

P0 = needed for the demo, P1 = makes it good, P2 = nice to have.

### 5.1 `GET /api/health`

```json
{ "status": "ok", "version": "0.1.0", "provider": "groq", "mock": false }
```

### 5.2 `GET /api/options`

```json
{
  "business_types": ["cafe", "restaurant", "gym", "salon", "other"],
  "default_city": "Islamabad",
  "areas": ["F-6", "F-7", "F-8", "F-10", "F-11", "G-9", "G-11", "E-7", "Blue Area", "DHA", "Bahria"],
  "default_competitors": ["Brew Bastion", "Chai Chowk", "Kahwa House", "Daily Grind ISB"],
  "sources": ["reddit", "web"],
  "modes": ["cached", "live"],
  "limits": { "max_urls": 10, "max_limit": 200 }
}
```

### 5.3 `GET /api/models`

```json
{
  "max_params_rule": "≤ 8B class (exact ≤ 8.5B), open-weight only",
  "provider": "groq",
  "tiers": {
    "small": { "id": "llama-3.1-8b-instant", "strategy": "compact prompt, low max_tokens" },
    "large": { "id": "llama-3.1-8b-instant", "strategy": "few-shot prompt + self-consistency" }
  },
  "models": [
    { "id": "llama-3.1-8b-instant", "provider": "groq", "nominal_size": "8B", "params_b": 8.03,
      "license": "Llama 3.1 Community License", "tier": "small|large", "open_weight": true, "eligible": true }
  ]
}
```

### 5.4 `GET /api/sources/status`

Follows Agent-Reach's "ordered backends, first working one wins" probe (`channels/base.py`, `channels/reddit.py`, `probe.py`).

```json
{
  "sources": [
    { "source": "reddit", "active": "exa",
      "backends": [
        { "name": "opencli", "status": "missing", "hint": "Needs OpenCLI + Chrome already logged in to reddit.com" },
        { "name": "rdt", "status": "missing", "hint": "pipx install 'git+https://github.com/public-clis/rdt-cli.git' then run `rdt login` yourself" },
        { "name": "exa", "status": "ok", "hint": "" },
        { "name": "snapshot", "status": "ok", "hint": "Cached data" } ] },
    { "source": "web", "active": "jina",
      "backends": [
        { "name": "exa", "status": "ok", "hint": "" },
        { "name": "jina", "status": "ok", "hint": "" },
        { "name": "snapshot", "status": "ok", "hint": "" } ] }
  ]
}
```

`status` is one of `ok | missing | broken | timeout | error` (same values as Agent-Reach `ProbeResult`).

### 5.5 `POST /api/runs`

Request:

```json
{
  "business": "cafe",
  "city": "Islamabad",
  "areas": ["F-7", "F-10"],
  "competitors": ["Brew Bastion", "Chai Chowk"],
  "sources": ["reddit", "web"],
  "mode": "cached",
  "urls": [],
  "limit": 100,
  "provider": null,
  "votes": 3
}
```

Only `business` is required; everything else falls back to `/api/options` defaults. `provider: null` means auto (from `.env`).

Response `202 Accepted`:

```json
{ "run_id": "r_20261010_1305_a1b2", "status": "queued" }
```

`409` if a run is already in progress (one run at a time keeps rate limits safe).

### 5.6 `GET /api/runs`

```json
{ "runs": [ { "run_id": "demo", "status": "done", "business": "cafe", "city": "Islamabad",
              "created_at": "2026-10-10T08:05:00Z", "posts": 78, "synthetic": true } ] }
```

### 5.7 `GET /api/runs/{run_id}`

```json
{
  "run_id": "r_20261010_1305_a1b2",
  "status": "running",
  "stage": "analyzing",
  "progress": { "done": 42, "total": 78 },
  "counts": { "collected": 81, "deduped": 79, "kept": 64, "filtered": 15, "escalated": 9, "failed": 0 },
  "messages": [ { "level": "warn", "text": "rdt not installed — Reddit via Exa site:reddit.com" } ],
  "created_at": "2026-10-10T08:05:00Z",
  "finished_at": null,
  "error": null
}
```

`status`: `queued | running | done | failed`. `stage`: `collecting | analyzing | trending | reporting | done`.

### 5.8 `GET /api/runs/{run_id}/results`

One payload for all dashboard tabs. `409` if the run isn't done yet.

```json
{
  "run_id": "demo",
  "provenance": {
    "synthetic": true, "mock": false,
    "sources_used": { "reddit": "snapshot", "web": "snapshot" },
    "provider": "groq", "models": ["llama-3.1-8b-instant"],
    "generated_at": "2026-10-10T08:06:10Z"
  },
  "overview": {
    "posts_analysed": 64, "relevant_pct": 0.81,
    "sentiment": { "pos": 18, "neg": 27, "neutral": 12, "mixed": 7 },
    "top_rising": { "term": "late-night hours", "lift": 4.1 },
    "escalation_rate": 0.14,
    "top_actions": [
      "Publish a 'Late-night cafés in F-7' page — demand up 4.1x, competitors criticised",
      "Answer 6 Reddit questions about backup power during load shedding",
      "Add sugar-free menu items and mention them on your Google profile"
    ]
  },
  "keywords": [
    { "term": "late night cafe f-7", "count": 9, "recent": 7, "baseline": 2, "lift": 4.1, "z": 2.3, "score": 36.9,
      "example": { "record_id": "demo014", "url": "https://reddit.example/r/islamabad/comments/demo014" } }
  ],
  "voice": {
    "pain_points": [ { "term": "slow wifi", "count": 11, "recent": 4, "baseline": 7, "lift": 0.9, "z": -0.2, "score": 9.9 } ],
    "requests":    [ { "term": "sugar-free options", "count": 6, "recent": 5, "baseline": 1, "lift": 3.6, "z": 1.9, "score": 21.6 } ],
    "questions":   [ { "record_id": "demo022", "source": "reddit", "text": "Any cafe in F-7 open after midnight with good wifi?",
                       "url": "https://reddit.example/r/islamabad/comments/demo022" } ]
  },
  "competitors": [
    { "name": "Brew Bastion", "mentions": 14, "pos": 3, "neg": 8, "neutral": 2, "mixed": 1, "negativity": 0.6,
      "top_complaints": ["slow service", "high prices"] }
  ],
  "gaps": [ { "theme": "late-night hours", "demand": 12, "negativity": 0.6, "gap": 7.2 } ],
  "content": {
    "briefs": [
      { "title": "Late-Night Cafés in F-7: Where to Work After 11 PM", "target_keyword": "late night cafe f-7",
        "outline": ["Why late-night matters in Islamabad", "Wi-Fi and backup power", "Our hours and menu"],
        "competitor_weakness": "Competitors close at 11 PM and lose power during load shedding" }
    ],
    "faqs": [ { "question": "Which cafes in F-7 are open after midnight?", "source_record_ids": ["demo022", "demo031"] } ],
    "faq_jsonld": "{\"@context\":\"https://schema.org\",\"@type\":\"FAQPage\",\"mainEntity\":[...]}"
  },
  "threads": [
    { "record_id": "demo022", "title": "Late night cafe with wifi?", "subreddit": "r/islamabad",
      "url": "https://reddit.example/r/islamabad/comments/demo022", "created_at": "2026-10-02T19:00:00Z",
      "question": "Any cafe in F-7 open after midnight with good wifi?", "relevance": 0.92 }
  ],
  "participation_note": "Answer helpfully, disclose that you own/work at the business, follow each subreddit's rules. Nothing is posted automatically.",
  "metrics": {
    "calls_by_tier": { "small": 55, "large": 18 }, "cache_hits": 0,
    "escalations": 9, "escalation_rate": 0.14, "repairs": 4, "schema_failures": 5, "schema_failure_rate": 0.07,
    "filtered": 15, "failed": 0,
    "tokens": { "prompt": 61234, "completion": 9876 },
    "latency_ms": { "p50": 420, "p95": 1310 }
  }
}
```

### 5.9 `GET /api/runs/{run_id}/posts`

Query params (all optional): `source=reddit|web`, `lang=en|ur|ur-Latn|mixed`, `tier=small|large`, `escalated=true|false`, `sentiment=pos|neg|neutral|mixed`, `status=ok|filtered|failed`, `q=<text search>`, `limit=50`, `offset=0`.

```json
{
  "total": 64, "limit": 50, "offset": 0,
  "items": [
    { "record_id": "demo014", "source": "reddit", "title": "Late night spots?", "snippet": "yaar F-7 mein koi cafe…",
      "lang": "ur-Latn", "tier": "large", "escalated": false, "sentiment": "neg", "status": "ok", "confidence": 0.82 }
  ]
}
```

### 5.10 `GET /api/runs/{run_id}/posts/{record_id}`

```json
{
  "record": { "id": "demo014", "source": "reddit", "url": "https://reddit.example/...", "title": "Late night spots?",
              "text": "yaar F-7 mein koi cafe raat 12 ke baad khula hota hai? [phone] pe call kiya koi jawab nahi",
              "created_at": "2026-10-03T21:10:00Z", "city": "Islamabad", "area": "F-7", "author_hash": "9f2c…", "lang": "ur-Latn" },
  "insight": { "relevant": true, "sentiment": "neg", "pain_points": ["late-night hours"], "requests": ["late-night hours"],
               "competitors_mentioned": [], "keywords": ["late night cafe f-7"], "question": "Is any cafe in F-7 open after 12?",
               "confidence": 0.82 },
  "trace": {
    "route": { "tier": "large", "reasons": ["lang=ur-Latn"] },
    "attempts": [
      { "model": "llama-3.1-8b-instant", "tier": "large", "kind": "extract", "valid": false, "error": "confidence: field required", "latency_ms": 510, "cached": false },
      { "model": "llama-3.1-8b-instant", "tier": "large", "kind": "repair", "valid": true, "error": null, "latency_ms": 380, "cached": false }
    ],
    "repairs": 1, "escalated": false, "votes": null
  }
}
```

`trace` is what makes the harness visible in the demo. The backend must keep each attempt in `AnalyzedRecord`.

### 5.11 Report downloads

`GET /api/runs/{run_id}/report.md` → `text/markdown`; `GET /api/runs/{run_id}/report.html` → `text/html`. Both are sent with `Content-Disposition: attachment`.

### 5.12 Eval (P2)

`POST /api/eval` with body `{ "provider": null }` runs synchronously on the ~30-item seed set and returns:

```json
{
  "labels_status": "provisional — verify by hand",
  "systems": [
    { "system": "baseline",   "relevance_f1": 0.71, "sentiment_acc": 0.55, "sentiment_macro_f1": 0.48, "pain_p": 0.50, "pain_r": 0.40, "latency_ms": 1,   "escalation_rate": 0.0,  "calls": 0 },
    { "system": "small-only", "relevance_f1": 0.0,  "sentiment_acc": 0.0,  "sentiment_macro_f1": 0.0,  "pain_p": 0.0,  "pain_r": 0.0,  "latency_ms": 0,   "escalation_rate": 0.0,  "calls": 0 },
    { "system": "large-only", "relevance_f1": 0.0,  "sentiment_acc": 0.0,  "sentiment_macro_f1": 0.0,  "pain_p": 0.0,  "pain_r": 0.0,  "latency_ms": 0,   "escalation_rate": 0.0,  "calls": 0 },
    { "system": "routed",     "relevance_f1": 0.0,  "sentiment_acc": 0.0,  "sentiment_macro_f1": 0.0,  "pain_p": 0.0,  "pain_r": 0.0,  "latency_ms": 0,   "escalation_rate": 0.0,  "calls": 0 }
  ]
}
```

(Numbers are placeholders.) `GET /api/eval/latest` returns the last result or `404`.

### 5.13 Draft reply (stretch)

`POST /api/runs/{run_id}/threads/{record_id}/draft-reply` with body `{ "business_name": "My Cafe", "tone": "friendly" }`:

```json
{ "draft": "If you're in F-7 we're open till 2 AM with a generator backup… (Disclosure: I run My Cafe.)",
  "model": "llama-3.1-8b-instant",
  "reminder": "Review and post it yourself. Keep the disclosure and follow r/islamabad rules." }
```

The draft always includes a disclosure line. There's no endpoint that posts to Reddit, by design.

## 6. Backend → harness mapping

| Endpoint | Calls into |
|---|---|
| `/api/models` | `pulse.harness.registry` (`Registry`, `resolve_tiers`) |
| `/api/sources/status` | `pulse.collectors.*.status()` (probe pattern adapted from Agent-Reach) |
| `POST /api/runs` | `pulse.pipeline.run(params, on_progress=...)` in a background thread: collect → normalize → `Extractor.analyze` → `trends.compute_trends` → `report.build_report` |
| `/results` | `out/runs/<id>/results.json` written by `report.build_report` (same data that renders `report.md`) |
| `/posts*` | `out/runs/<id>/insights.jsonl` (`AnalyzedRecord` incl. `trace`) |
| `/api/eval` | `pulse.eval.run_eval` |

The CLI (`pulse run`) and the API share `pulse.pipeline.run`, so there's exactly one code path to test.

## 7. Frontend files

```
frontend/
├── index.html        # all four screens as <section>s, hash routing (#/new, #/run/<id>, #/results/<id>, #/harness)
├── app.js            # fetch wrapper (+ ?mock=1 → frontend/mock/*.json), polling, rendering via textContent
├── styles.css        # layout, cards, tabs, CSS bar charts, badges
└── mock/
    ├── options.json  models.json  sources_status.json
    ├── run_status.json  results.json  posts.json  post_detail.json
```

The mock JSON files must match the examples in section 5, so the frontend works before the backend is ready.
