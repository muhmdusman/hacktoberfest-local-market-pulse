# Build Plan — Local Market Pulse (150-minute build window)

Context and fixed decisions: [CONTEXT.md](CONTEXT.md). Dashboard + API contract: [UI_AND_API.md](UI_AND_API.md). Rules: [../rules-hackathon.md](../rules-hackathon.md).

**Golden rule:** first get one complete flow working: dashboard "Quick demo" → `/api/runs` → report shown in tabs. The CLI `pulse run --cached` is the same pipeline and is our demo backup. Polish comes after. A small thing that works beats a big thing that doesn't.

**Reuse rule:** before writing any collector or tool-runner, open the matching Agent-Reach file listed in CONTEXT.md → "Reusing Agent-Reach" and adapt it with attribution. Spend build time on the harness, dashboard and skill, not on re-solving Reddit access.

## Timeline (three parallel tracks)

| Min | Backend track (A + B) | Frontend & Skill track (C) | Done when |
|---|---|---|---|
| 0–10 | Item 1 scaffold, claim API credits | Skeleton `frontend/` + mock JSON (item 14a) | `pulse models` runs; `/?mock=1` opens |
| 10–80 | Items 2–8: schemas, snapshot, collectors (adapted), harness, trends, report, pipeline, CLI | Item 14b: all screens rendering from mock JSON | `pulse run --cached --provider mock` writes report + `results.json`; UI shows all tabs from mocks |
| 80–100 | Item 13: FastAPI P0 endpoints + `pulse serve` | Item 10: Agent Skill | UI works against the real API on the `demo` run |
| 100–115 | Item 8b: real Groq run, cache it. Item 13 P1 endpoints | Item 14c: switch off mocks, posts drawer, harness screen | Full flow with the real model |
| 115–130 | Item 9: eval | Item 11: README + screenshots | `pulse eval` table; README complete |
| 130–140 | **Freeze:** tests, secrets check, push, repo public, MLH form | | Freeze checklist ticked |
| 140–150 | Demo rehearsal (script at bottom) | | |

## Roles (team of up to 3)

| Role | Owns | Items |
|---|---|---|
| **A: Data** | collectors (adapted from Agent-Reach), normalization, demo snapshot, trends | 2, 3, 4, 7 (trends), 12, eval labels |
| **B: Harness** (lead) | registry, providers, router, extract, cache, metrics, pipeline, CLI, API | 1, 5, 6, 8, 8b, 13, 9 |
| **C: Product** | dashboard, report rendering, Agent Skill, README, demo, MLH form | 14, 7 (report), 10, 11, submission |

Solo or pair: B's items first, then A's, then C's. Commit small and often to `main`, and pull before every push. Frontend and backend meet only through [UI_AND_API.md](UI_AND_API.md). Change that file first if a field must change.

## Cut list (cut from the top when behind)

1. Draft-reply endpoint + button (stretch)
2. Self-consistency votes
3. `GET /api/sources/status` (show a static "using saved data" badge instead)
4. Screen 4 "Under the hood" (keep metrics on the Overview tab)
5. Posts explorer drawer (keep the table)
6. Live collection (cached snapshot is enough for the demo)
7. Eval rows beyond `baseline` + `routed`

**Never cut:** 8B registry gate, repair + escalation, tests, dashboard Screens 1–3 with the `demo` run, README "built vs reused" section, SKILL.md, secrets hygiene.

## Fixed implementation decisions

1. **Env:** `uv venv --python 3.12 .venv` then `uv pip install --python .venv/bin/python -e '.[dev]'`. Build backend hatchling. Runtime deps: `httpx`, `pydantic`, `python-dotenv`, `fastapi`, `uvicorn`. Dev: `pytest`. **Pin the exact versions uv resolves** in `pyproject.toml`. CLI uses stdlib `argparse`.
2. **Commands:** TEST = `.venv/bin/python -m pytest -q`; RUN = `.venv/bin/pulse run --cached --provider mock`; SERVE = `.venv/bin/pulse serve` (127.0.0.1:8000).
3. **Concurrency:** sync `httpx.Client` + `ThreadPoolExecutor` bounded by `LLM_MAX_CONCURRENCY` (default 4). The API runs the pipeline in one background thread, one run at a time (409 if busy).
4. **Provider selection:** `--provider {mock,openai,ollama}` > env `LLM_PROVIDER` > `openai` if `LLM_API_KEY` set, else `mock`. The CLI, report and dashboard banner must say clearly when mock is used ("MockProvider: deterministic test stand-in, not a real model").
5. **Model registry & 8B cap.** Each entry has `id, provider, nominal_size ("8B"), params_b (exact), license, tier, open_weight`. Rule: **reject if the nominal size class is above 8B or the exact count is above 8.5B, or if the model isn't open-weight.** That accepts the 8B class the organizers name as eligible (Llama 3.1 8B = 8.03B) and rejects 9B+, 14B, 32B, 70B. Defaults:
   - Groq (`LLM_BASE_URL=https://api.groq.com/openai/v1`): `llama-3.1-8b-instant` (8B class, 8.03B, Llama 3.1 Community License) for both tiers. Small = compact prompt with a low `max_tokens`. Large = full few-shot prompt + self-consistency.
   - OpenRouter: small `meta-llama/llama-3.2-3b-instruct` (3.21B), large `qwen/qwen-2.5-7b-instruct` (7.61B, Apache-2.0).
   - Ollama: small `qwen3:1.7b` (2.03B), large `qwen3:4b` (4.02B), Apache-2.0.
   - Mock: `mock-small`, `mock-large`.
   - Overridable via `LLM_MODEL_SMALL` / `LLM_MODEL_LARGE`; ids must exist in the registry, else a clear error.
6. **Fictional competitors** in synthetic data ("Brew Bastion", "Chai Chowk", "Kahwa House", "Daily Grind ISB") so fake complaints never target real businesses. Synthetic URLs use the reserved `.example` TLD.
7. **Artifacts** per run in `out/runs/<run_id>/`: `run.json`, `records.jsonl`, `insights.jsonl` (AnalyzedRecord incl. `trace`), `metrics.json`, `results.json` (the exact `/results` payload from UI_AND_API.md §5.8), `report.md`, `report.html`. The CLI writes the same files (run id `cli_<timestamp>`, or `demo` for the cached demo). LLM cache in `.cache/llm/<sha256>.json`.
8. **Snapshot format:** line 1 is `{"_meta": {"synthetic": true|false, "description": "...", "created": "...", "business": "cafe", "city": "Islamabad"}}`, then raw posts `{id, source, url, title, text, created_at, author, area, subreddit?, parent_id?}`. Raw `author` exists only in snapshot input; normalized records keep only `author_hash`.
9. **Data access: adapt from Agent-Reach** (file map in CONTEXT.md → "Reusing Agent-Reach"):
   - Reddit backend order: `opencli` (only if Chrome is already logged in; we never automate login) ▸ `rdt` ▸ Exa `site:reddit.com` ▸ snapshot.
     - OpenCLI: `opencli reddit search "<q>" -f yaml`, `opencli reddit read <ID> -f yaml`, `opencli reddit subreddit islamabad -f yaml`
     - rdt: `rdt search "<q>" --limit N`, `rdt read <ID>`, `rdt sub islamabad --limit 20`. Try `--yaml`/`--json`; if parsing fails, fall through.
     - Never run `rdt login`, never read cookies.
   - Reddit flow: search + subreddit browse → dedupe IDs → read top N posts **with comments** → post and each substantive comment become Records.
   - Search: `mcporter call exa.web_search_exa query="<q>" numResults=N`. Parse JSON, else regex the `Title:`/`URL:`/`Text:` blocks.
   - Page text: Jina Reader `https://r.jina.ai/<URL>` (`Accept: text/plain`, 30 s timeout, 5 MB cap) + anti-bot detection, adapted from `channels/web.py`. All user URLs pass the public-URL guard from `utils/url.py`. Split long pages into chunks of about 1,500 characters.
   - Subprocesses: list argv (no shell), timeout, UTF-8 env (`utils/process.py`), statuses `ok/missing/broken/timeout/error` (`probe.py`).
   - Fallback chain is always: tool → next tool → cached snapshot, with a clear message and install hint (shown in the progress screen).
10. **Gap score:** `gap = demand × negativity`. demand = records whose requests or pain_points contain the theme. negativity = `(neg_or_mixed + 1) / (n + 2)` over records mentioning a competitor AND the theme (0.5 with no evidence).
11. **Trend windows** are relative to the newest `created_at`: recent = last 30 days, baseline = older. `lift = (recent_rate + 0.01) / (baseline_rate + 0.01)`, z = two-proportion z-score, opportunity = frequency × lift. The UI shows "↑ rising" when lift > 1.5.
12. **FAQ JSON-LD** answers are placeholders ("Draft your answer here — verify facts before publishing"). The model never invents business facts. Draft replies always include a disclosure line, and nothing posts automatically.

## Task checklist

### Phase A: backend core flow

- [ ] **1. Scaffold** (B, ~8 min). `pyproject.toml` (name `local-market-pulse`, `requires-python>=3.12`, script `pulse = "pulse.cli:main"`, hatch `packages=["pulse"]`, pytest `testpaths=["tests"]`). `.gitignore`: `.env .venv/ out/ .cache/ __pycache__/ *.pyc .pytest_cache/ .agents/`. `.env.example` placeholders only: `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_API_KEY=your-key-here`, `LLM_MODEL_SMALL`, `LLM_MODEL_LARGE`, `OLLAMA_BASE_URL`, `LLM_MAX_CONCURRENCY`, `LLM_TIMEOUT_S`, `PULSE_CONFIDENCE_THRESHOLD`. `pulse/config.py` loads `.env` into a frozen `Settings`. Copy `../Agent-Reach/LICENSE` to `third_party/agent-reach-LICENSE`. **Keep the existing `LICENSE` unchanged.**
  Verify: `.venv/bin/python -c "import pulse, httpx, pydantic, dotenv, fastapi"`.
- [ ] **2. Schemas, lexicon, normalization** (A, ~10 min). `pulse/schema.py`: `Record`, `Insight` (`extra="forbid"`, confidence 0–1), `ContentBrief` (outline ≥3), `Attempt` (model, tier, kind extract/repair/vote/brief, valid, error, latency_ms, cached), `AnalyzedRecord` (record, insight, route, attempts, repairs, escalated, status ok / filtered / failed). `pulse/lexicon.py`: café keywords, Islamabad area tokens (F-6, F-7, F-10, G-9, G-11, E-7, Blue Area, Jinnah Super, Centaurus, Giga Mall…), ~60 Roman-Urdu words, EN + Roman-Urdu sentiment lexicon, pain-point synonym map → canonical labels, `canonicalize()`. `pulse/normalize.py`: `scrub_pii` (emails, `+92 3xx…`, `0092…`, `03xx-xxxxxxx`, long digit runs), `hash_author` (sha256), `normalize`, `dedupe` (url + normalized-text hash).
  Verify: `tests/test_normalize.py`.
- [ ] **3. Demo snapshot** (A, ~10 min). `data/snapshots/demo_islamabad_cafes.jsonl`: `_meta` with `synthetic: true` + ~80 items over ~90 days (≥25 in the newest 30), including Reddit posts *and* comments (`parent_id`). Language mix: ~55% English, ~30% Roman Urdu / code-mixed, ~15% Urdu script. Source mix: ~55% Reddit, ~45% web. Include competitor complaints, requests, ~15 questions, ~8 off-topic posts, 3–4 fake PII strings, 2 near-duplicates. Recent-window trends to seed: late-night hours, no backup power (load shedding), sugar-free options. Baseline trends: high prices, slow service.
- [ ] **4. Collectors, adapted from Agent-Reach** (A, ~12 min). `pulse/collectors/_agent_reach_probe.py` (probe_command/ProbeResult + UTF-8 env), `_agent_reach_web.py` (Jina read + anti-bot), `_agent_reach_url.py` (public-URL guard), each with the attribution header from CONTEXT.md. Our own `base.py` (ordered backends + `status()`), `snapshot.py`, `reddit.py` (decision 9 order + post/comment flow), `web.py` (Exa or `--urls` → Jina → chunks). `--cached` (default) / `--live`.
  Verify: `tests/test_collectors.py` (missing tools → snapshot fallback + install hint; Exa text parser; anti-bot detection; private-IP URL rejected; `status()` returns `ok/missing` per backend).
- [ ] **5. Harness core** (B, ~15 min, original). `pulse/harness/registry.py` (decision 5, `ModelTooLargeError`, `resolve_tiers`), `providers.py` (OpenAI-compatible with a `response_format` json_object attempt, Ollama `format=json`, retries with backoff + jitter on 429/5xx/timeout, semaphore), `mock.py` (deterministic, lexicon-based; knobs `invalid_json_first_n`, `small_low_confidence_on_mixed`), `cache.py`, `metrics.py` (calls per tier, cache hits, escalations, schema failures, repairs, tokens, p50/p95).
  Verify: `tests/test_registry.py` (70B, 14B, 9B rejected; 8B class + 7.61B accepted; closed model rejected; unknown id error), `tests/test_providers.py` (503 then success via `httpx.MockTransport`, Groq base URL).
- [ ] **6. Router + extraction** (B, ~15 min, the centerpiece, original). `router.py`: `detect_lang` (Urdu script ratio ≥0.3 → `ur`; Roman-Urdu token ratio thresholds → `ur-Latn` / `mixed`; else `en`), `prefilter`, `route` (large tier for ur / ur-Latn / mixed / >800 chars / mixed-sentiment lexicon hits, with `reasons`). `extract.py`: prompt (JSON-only, field definitions, canonical label list, one Roman-Urdu few-shot) → parse (strip fences, first balanced `{}`) → validate → ≤2 repair prompts → escalate → `failed`. Self-consistency on borderline confidence. Canonicalize labels. **Record every call as an `Attempt`.** Shared `generate_json()` reused for briefs and draft replies. Parallel `analyze(records, on_progress)` with stable order.
  Verify: `tests/test_router.py`, `tests/test_extract.py` (Roman Urdu → large; junk filtered; repairs==1 with 2 attempts recorded; escalated; always-invalid → failed; second run hits cache).
- [ ] **7. Trends + report** (A trends, C report, ~12 min). `pulse/trends.py` (decisions 10–11). `pulse/report.py`: 3–5 `ContentBrief`s via the large tier, plus `top_actions` (3 plain-language actions from the top gaps and keywords). Builds the `results.json` payload exactly per UI_AND_API.md §5.8, then renders `report.md` + standalone `report.html` from it (inline CSS, `html.escape` everything, JSON-LD via `json.dumps`). Sections: provenance + SYNTHETIC/Mock banners, models with size/license/provider, keyword opportunities, FAQ + JSON-LD, content briefs, competitor gaps, Reddit threads worth answering + honest-participation note, harness metrics.
  Verify: `tests/test_trends.py` (3/10 recent vs 1/20 baseline → lift ≈ 5.17), `tests/test_report.py` (escapes `<script>`, JSON-LD parses, `results.json` has every §5.8 key).
- [ ] **8. Pipeline + CLI + end-to-end** (B, ~8 min). `pulse/pipeline.py`: `run(params, on_progress) -> run_id`. Stages collecting → analyzing → trending → reporting → done, writes decision-7 artifacts and `run.json` status. `pulse/cli.py`: `collect | analyze | report | run | eval | models | serve`. Defaults: cafe, Islamabad, fictional competitors, reddit+web, `--cached`. Print a summary.
  Verify: `tests/test_e2e.py` + RUN finishes in <30 s. **CHECKPOINT: backend demo works.**

### Phase B: API, real model, eval, skill, docs

- [ ] **13. FastAPI server** (B, ~15 min). `pulse/api/server.py` + `jobs.py` implementing UI_AND_API.md §5. Do the P0 endpoints first (health, options, models, POST/GET runs, results, report downloads), then P1 (runs list, posts list/detail, sources/status), then P2 (eval). Serve `frontend/` at `/`, build the `demo` run on startup if missing, use the §4 error format, bind 127.0.0.1, URL guard + limits, never return keys.
  Verify: `tests/test_api.py` with FastAPI `TestClient`: POST a cached mock run → poll until done → `/results` keys match §5.8, `/posts/{id}` has `trace.attempts`, 404/409/422 shapes, private-IP URL → 422.
- [ ] **8b. Real-model smoke run** (B, ~10 min, needs the key). Put the Groq key in `.env` (never commit it). Run `pulse models`, `pulse run --cached`, then the dashboard quick demo. Check the outputs read well, tune prompts if needed. Keep `.cache/llm/` so the demo replays instantly.
- [ ] **9. Eval** (B, ~12 min). `data/eval/label_template.jsonl`, `data/eval/seed_eval.jsonl` (~30 items, `label_status: "provisional — verify by hand"`). `pulse/eval.py`: systems `baseline` (lexicon only), `small-only`, `large-only`, `routed`. Metrics: relevance F1, sentiment accuracy + macro-F1, pain-point precision/recall, latency per item, escalation rate, calls. Writes `out/eval.md` + `out/eval.json` (shape per §5.12).
  Verify: `tests/test_eval.py`.

### Frontend track (C, in parallel from minute 0)

- [ ] **14a. Skeleton + mocks** (~10 min). `frontend/index.html`, `app.js`, `styles.css`, plus `frontend/mock/*.json` copied from the UI_AND_API.md §5 examples. `?mock=1` makes `app.js` read the mocks instead of `/api`. Hash routing `#/new`, `#/run/<id>`, `#/results/<id>`, `#/harness`.
- [ ] **14b. Screens 1–3 on mocks** (~45 min). New-scan form (labels, defaults from `/api/options`, model badge), progress stepper with polling, results tabs: Overview (KPIs, top actions, provenance banner), Keywords (table + rising badge + copy), Customer voice (CSS bar charts + questions), Competitors (table + gaps), Content plan (brief cards + copy Markdown + copy JSON-LD), Reddit threads (list + participation note), Posts table. Render all text with `textContent`.
- [ ] **14c. Real API + extras** (~20 min). Remove `?mock=1` from the default path and test against `pulse serve` with the `demo` run. Add the posts drawer (insight JSON + trace), Screen 4 (models, metrics, eval table + "Run evaluation"), report download buttons, error states. Check keyboard tab navigation and that sentiment is shown as text, not only colour.
  Verify: in a browser, Quick demo → progress → results with every tab populated; no console errors; a screenshot of each screen saved to `docs/screenshots/` for the README.

### Skill & docs (C)

- [ ] **10. Agent Skill** (C, ~12 min), per [agentskills.io/specification](https://agentskills.io/specification), structure inspired by Agent-Reach `skill/SKILL_en.md`. Draft frontmatter:
  ```yaml
  ---
  name: local-market-pulse
  description: >-
    Local market listening and SEO opportunities for small businesses. Collects what people in a city say on
    Reddit and the web about a business category (e.g. cafes in Islamabad), uses open-weight models of 8B
    parameters or fewer to extract pain points, requests, competitor complaints, local keywords and real
    questions, then produces an SEO action report with keyword opportunities, FAQ schema, content briefs and
    Reddit threads worth answering. Use when the user asks about local SEO, trending products or services in a
    city or neighbourhood, competitor reviews, customer pain points, social listening, or content ideas for an SME.
  license: MIT
  compatibility: Python 3.12+ with uv. Network access for live mode. Needs an OpenAI-compatible endpoint serving open-weight models of 8B parameters or fewer (e.g. Groq llama-3.1-8b-instant) or local Ollama. Optional rdt-cli, OpenCLI or mcporter for live Reddit/web search.
  metadata:
    version: "0.1.0"
    domain: "05 Business & Productivity"
    max-model-params: "8B"
  ---
  ```
  Body (<500 lines): when to use, step-by-step (install, `.env`, `scripts/run_pulse.sh --business cafe --city Islamabad`, read `out/runs/<id>/report.md`, or `pulse serve` for the dashboard), worked example (input → excerpt of keywords, one FAQ, one brief), edge cases (no key → mock + disclaimer; tools missing → snapshot; Roman Urdu; tiny datasets make lift unreliable; never auto-post). Files: `scripts/run_pulse.sh`, `references/HARNESS.md`, `references/DATA_SOURCES.md`, `references/REPORT_FORMAT.md`, `assets/example_report.md`. Add `pulse/__main__.py`.
  Verify: `uvx --from skills-ref skills-ref validate skills/local-market-pulse` + `tests/test_skill_spec.py` (local rule check).
- [ ] **11. README** (C, ~10 min). Project name + one-liner; domain; target user; problem; solution and core features. Dashboard screenshots. AI component: exact model name, parameter size, runtime/provider, what it does, ≤8B enforcement. Mermaid **architecture**, **data-flow** and **sequence** diagrams (UI → API → pipeline → harness → model). "What we built vs. what we reused" (incl. the adapted Agent-Reach files). Setup (deps, install, env var names, `pulse serve`, `pulse run`, minimal example). **Testing & findings** table (scenario, input, expected, actual, pass/fail), eval results, known limitations. Responsible use. Team names + contributions. License. Acknowledgements (Agent-Reach, rdt-cli, OpenCLI, Exa, Jina, Meta Llama, Qwen, Groq, FastAPI). Also disclose the AI-assisted development tools we used.
- [ ] **12. Optional real web data** (A, ≤10 min). `pulse collect --live --sources web --urls urls.txt` with 3–5 public Islamabad café review pages. Save as `data/snapshots/live_web_<date>.jsonl` with `synthetic: false`.

## Freeze checklist (minute 130)

- [ ] `pytest -q` green; `pulse serve` → Quick demo works end to end in the browser; `pulse run` works from a clean clone
- [ ] `git check-ignore .env` prints `.env`; no keys found by `grep -rEn "gsk_|sk-[A-Za-z0-9]{20,}" --exclude-dir=.venv .`
- [ ] README renders on GitHub (Mermaid diagrams + screenshots show), LICENSE + `third_party/agent-reach-LICENSE` present, repo **public**
- [ ] MLH form: title, description (problem, product, main feature, AI used), GitHub URL
- [ ] Team names and contributions in README

## Demo script (3 minutes)

1. **Problem (20 s):** Islamabad cafés can't afford $100/month listening tools, and Reddit threads shape both Google and AI answers.
2. **Dashboard (60 s):** fill the form (café, Islamabad, F-7), click "Find opportunities", watch the stepper. Point out the model badge "Llama 3.1 8B via Groq · ≤8B ✓" and the escalation counter.
3. **Results (60 s):** top actions → rising keyword "late night cafe F-7" → competitor gap → copy FAQ JSON-LD → Reddit threads worth answering. Open one Roman-Urdu post in the explorer to show tier, repair and escalation.
4. **Proof (30 s):** Under the hood: models table (70B is rejected), harness metrics, eval table (routed vs. baseline vs. single tier).
5. **Close (10 s):** open-source MIT, Agent Skill for any agent, CLI too. Roadmap: more platforms, Search Console link, site generator.
