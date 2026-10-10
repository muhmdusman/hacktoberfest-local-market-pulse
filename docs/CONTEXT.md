# Project Context — Local Market Pulse

Read this first. It explains what we are building, why, and the decisions already made, so every teammate (and every AI coding assistant) works from the same picture.

| Doc | What it's for |
|---|---|
| [PLAN.md](PLAN.md) | Step-by-step build plan, owners, checklist |
| [UI_AND_API.md](UI_AND_API.md) | Dashboard screens + API endpoints (frontend ↔ backend contract) |
| [../rules-hackathon.md](../rules-hackathon.md) | Event rules and judging criteria |

## One-liner

An open-weight AI harness and Agent Skill that listens to what people in a city say about a business category on Reddit and the web, then turns it into an SEO action report for small businesses.

## Problem

SMEs in Islamabad (cafés, gyms, salons, clinics) can't afford social-listening or SEO-trend tools (Brandwatch, Semrush, Ahrefs: $100+/month). They don't know:

- which local search phrases people actually use ("late night cafe F-7", "sasta biryani G-11"),
- what customers complain about at competitors,
- which questions go unanswered, and which products or services are missing.

Reddit threads matter a lot here. They rank highly in Google and are often quoted by AI assistants (ChatGPT, Claude, Perplexity), so they're both a data source and a visibility channel.

## Solution (MVP scope for today)

```
Dashboard (frontend/)  ⇄  FastAPI (pulse/api/)  →  pipeline
collect (Reddit + Web)  →  normalize & scrub PII  →  HARNESS (open-weight ≤8B models)
   →  trends & gap scoring  →  SEO action report (dashboard + MD/HTML)  →  eval table
```

Three ways to use it, all running the same `pulse.pipeline.run` code path:

1. **Dashboard** for shop owners: one form, "Find opportunities", results in tabs (see [UI_AND_API.md](UI_AND_API.md)).
2. **CLI** (`pulse run`) for the team and for the demo backup.
3. **Agent Skill** (`skills/local-market-pulse/`) for AI agents.

The report contains:

1. **Keyword opportunities**: local phrases ranked by frequency × recent lift.
2. **FAQ list**: real questions people ask, plus FAQPage JSON-LD for the SME's site.
3. **Content briefs** (written by the model): title, target keyword, outline, competitor weakness addressed.
4. **Competitor gap table**: complaints per competitor, plus demand nobody serves.
5. **Reddit threads worth answering**, with an honest-participation note (no auto-posting).
6. **Harness metrics**: models used, escalation rate, repairs, latency.

Out of scope today (roadmap slide only): more platforms (Facebook, X, YouTube, Google reviews), user accounts/auth, static-site generator, posting automation, connecting our earlier Search Console SEO tool.

## Who it's for

- Primary: SME owners and marketers in Islamabad. Demo vertical: **cafés in Islamabad**.
- Secondary: AI agents, via the Agent Skill (`skills/local-market-pulse/`), so any skills-compatible agent can run the analysis.

## How we score (judging weights from the rules)

| Criterion | Weight | How we earn it |
|---|---|---|
| Technical implementation | 30% | Working end-to-end CLI, tests, routing, validation, retries, cache, metrics |
| Open-weight AI usage | 25% | The model does all the classification, extraction and brief writing. Remove it and nothing works |
| Originality | 20% | Roman-Urdu/code-mix aware router, small→large escalation, 8B-cap registry, eval comparison |
| Usefulness & impact | 15% | Concrete SEO actions for local SMEs, Islamabad-specific |
| Open-source quality & demo | 10% | MIT, README with diagrams, test findings, Agent Skill that follows the standard |

## Fixed decisions (don't re-debate during the build)

| Topic | Decision |
|---|---|
| Approach | **Model harness + Agent Skill**, combined (both allowed by the rules) |
| Domain | 05 Business & Productivity (with a community angle for local SMEs) |
| Sources today | **Reddit + Web only**. More platforms later |
| Model cap | **≤ 8B parameters**, local or hosted (rule from the Participant Manual). Enforced in code by the model registry |
| Primary inference | Hosted OpenAI-compatible API with event credits. Default: **Groq `llama-3.1-8b-instant`** (Llama 3.1 8B, named as an eligible example in the manual). Verify availability when claiming credits |
| Fallback inference | Ollama local (`qwen3:1.7b` / `qwen3:4b`, Apache-2.0); OpenRouter (`llama-3.2-3b-instruct`, `qwen-2.5-7b-instruct`) |
| Test inference | `MockProvider`, a deterministic stand-in model, so tests and the demo run with no key and no network |
| Orchestration | **Our own Python code.** No LangChain / LlamaIndex / DSPy / instructor / outlines. Only `httpx`, `pydantic`, `python-dotenv` (+ `pytest`) for the harness |
| UI | Static HTML + vanilla JS dashboard in `frontend/`, served by a **FastAPI** backend in `pulse/api/`. No build step, works offline. Contract: [UI_AND_API.md](UI_AND_API.md) |
| Python | 3.12 via `uv` (system Python 3.14 is too new for some wheels) |
| Agent-Reach | **Reuse, don't rewrite.** Data access (Reddit, web, search, tool health checks) is adapted from Agent-Reach with MIT attribution. See "Reusing Agent-Reach" below. The harness stays 100% ours |
| Reddit access order | OpenCLI (existing logged-in Chrome) ▸ rdt-cli ▸ Exa `site:reddit.com` ▸ cached snapshot. Same order as Agent-Reach `channels/reddit.py` |
| Demo data | Cached snapshot so the demo works offline. If synthetic, it's labelled **SYNTHETIC DEMO DATA** everywhere and uses **fictional** competitor names |
| Reddit ethics | Report only lists threads worth answering. Humans answer, disclose affiliation, follow subreddit rules. Nothing posts automatically |
| Privacy | Usernames are SHA-256 hashed, emails and phone numbers scrubbed before any model call |
| Secrets | `.env` is git-ignored; only `.env.example` with placeholders is committed |

## Original work vs. reused (judges check this)

| Ours (original) | Reused (credited) |
|---|---|
| `pulse/harness/`: registry with 8B gate, providers (OpenAI-compatible, Ollama, Mock), router (Roman Urdu / Urdu script / code-mix detection, relevance pre-filter, tier routing), extraction loop (JSON schema validation → repair retries → escalation → self-consistency votes), result cache, run metrics, per-post trace | Agent-Reach (MIT): backend-probe pattern, Reddit/web/search commands, Jina reader + anti-bot check, public-URL guard, UTF-8 subprocess env. Adapted into clearly labelled `pulse/collectors/_agent_reach_*.py` files |
| `pulse/trends.py`: lift, z-score, gap scoring | rdt-cli / OpenCLI (Reddit), mcporter + Exa (search), Jina Reader (page → text) |
| `pulse/pipeline.py`, `pulse/report.py`, `pulse/eval.py`, `pulse/cli.py`, `pulse/api/`, `frontend/` dashboard, PII scrubbing | Open-weight models (Meta Llama, Qwen), hosted runtime (Groq / OpenRouter / Ollama) |
| `skills/local-market-pulse/` Agent Skill, demo dataset, eval labels | httpx, pydantic, python-dotenv, FastAPI, uvicorn, pytest |

## Reusing Agent-Reach (don't write data access from scratch)

Agent-Reach (`/home/usman/Desktop/hacktoberfest/Agent-Reach`, MIT, © 2025 Agent Eyes) has already solved "how do I read Reddit and the web reliably". Before writing a collector, open the matching file below and adapt it.

| We need | Look at (in `Agent-Reach/agent_reach/`) | What to take |
|---|---|---|
| Ordered backends, first working one wins, with fix hints | `channels/base.py` (`Channel.ordered_backends`, `check`) | The pattern for our `collectors/base.py` and `GET /api/sources/status` |
| Reddit backend detection | `channels/reddit.py` (`_check_opencli`, `_check_rdt`, login hint) | Probe order and hint text. **Don't copy cookie handling**: we never read cookies or log in |
| Reddit commands | `skill/references/social.md` → "Reddit" | `opencli reddit search "q" -f yaml`, `opencli reddit read ID -f yaml`, `opencli reddit subreddit islamabad -f yaml`; `rdt search "q" --limit N`, `rdt read ID`, `rdt sub islamabad --limit 20` (`--yaml` output) |
| Web search | `channels/exa_search.py`, `skill/references/search.md` | `mcporter call exa.web_search_exa query="..." numResults=N` (`site:reddit.com` for the Reddit fallback) |
| Read any web page | `channels/web.py` (`read`, `_is_antibot_page`) | Jina Reader call `https://r.jina.ai/<URL>` + Cloudflare/anti-bot detection |
| Safe URL input (API accepts URLs) | `utils/url.py` (`normalize_public_http_url`, `host_matches`) | Blocks private/loopback targets (SSRF guard) |
| Running CLI tools | `probe.py` (`probe_command`, `ProbeResult`), `utils/process.py` (`utf8_subprocess_env`) | Timeouts, `ok/missing/broken/timeout/error` statuses, forced UTF-8 (needed for Urdu text) |
| Clean logs | `utils/text.py` (`scrub_url_credentials`) | Redact credentials from messages |
| Skill layout | `skill/SKILL_en.md`, `skill/references/` | Progressive-disclosure structure for our SKILL.md |

**Rules for reuse**

1. Put adapted code in files named `pulse/collectors/_agent_reach_*.py`, each starting with: `# Adapted from Agent-Reach (https://github.com/Panniantong/Agent-Reach), MIT License, Copyright (c) 2025 Agent Eyes. Changes: <what we changed>.`
2. Copy Agent-Reach's license to `third_party/agent-reach-LICENSE`, and credit it in README → Acknowledgements and "What we built vs. reused".
3. Take only what we need (small functions), not the whole package. Translate Chinese comments and messages to English.
4. **Never adapt code into `pulse/harness/`.** That's our original contribution and the part judged as the harness.

## Reddit read flow

```
queries = business+city ("cafe Islamabad"), area phrases ("cafe F-7"), "<competitor> review",
          question patterns ("best cafe in Islamabad", "late night cafe Islamabad")
   + subreddit browse: r/islamabad, r/pakistan
→ backend = first working of: opencli ▸ rdt ▸ exa(site:reddit.com) ▸ snapshot
→ search/browse → collect post IDs/URLs (dedupe) → read top N posts WITH comments
→ every post and every substantive comment becomes a Record (comments hold the answers and complaints)
→ normalize: scrub PII, hash author, detect language → harness
```

The web flow is the same shape: Exa search (or user-supplied URLs) → Jina Reader → split long pages into chunks of about 1,500 characters → Records.

The open-weight model is the core in both flows. Collectors only fetch text. Every judgement (relevance, sentiment, pain points, requests, keywords, questions, briefs, reply drafts) comes from the ≤8B model through our harness.

## How the harness routes a post

1. **Pre-filter:** drop posts unrelated to the business, city or competitors (cricket, politics, rent).
2. **Language detection:** `en`, `ur` (Urdu script), `ur-Latn` (Roman Urdu), `mixed`.
3. **Route:** plain short English goes to the **small tier**. Urdu, Roman Urdu, code-mixed, long or ambiguous posts go to the **large tier**.
4. **Extract:** the model returns JSON (`Insight`: relevant, sentiment, pain_points, requests, competitors, keywords, question, confidence), which is validated with pydantic.
5. **Repair:** invalid JSON gets up to 2 repair prompts that include the validation error.
6. **Escalate:** if the small tier is still invalid or confidence < 0.6, the post is re-run on the large tier.
7. **Self-consistency:** on borderline confidence, take a majority vote over N samples.
8. **Cache and metrics:** every call is cached by hash (fast, reproducible demo) and counted.

If the provider has only one ≤8B model (for example Groq with only Llama 3.1 8B), both tiers use the same model with different strategies. Small = short prompt with a low token budget. Large = full few-shot prompt plus self-consistency votes. Routing still decides how much compute each post gets.

## Repository layout (target)

```
hacktoberfest-local-market-pulse/
├── README.md                 # judge-facing: problem, AI component, diagrams, setup, demo, test findings
├── LICENSE                   # MIT
├── rules-hackathon.md        # event rules summary
├── docs/CONTEXT.md           # this file
├── docs/PLAN.md              # build plan + task checklist
├── docs/UI_AND_API.md        # dashboard screens + API contract
├── pyproject.toml  .env.example  .gitignore
├── pulse/
│   ├── cli.py config.py schema.py lexicon.py normalize.py pipeline.py trends.py report.py eval.py
│   ├── collectors/  base.py snapshot.py reddit.py web.py _agent_reach_*.py (adapted, attributed)
│   ├── harness/     registry.py providers.py mock.py router.py extract.py cache.py metrics.py   (100% original)
│   └── api/         server.py jobs.py   (FastAPI, serves frontend/ at /)
├── frontend/        index.html app.js styles.css mock/*.json
├── skills/local-market-pulse/  SKILL.md scripts/ references/ assets/
├── third_party/     agent-reach-LICENSE
├── data/snapshots/  data/eval/
└── tests/
```

## Glossary

- **Tier:** small or large model slot in the router.
- **Escalation:** re-running a post on the large tier after a low-confidence or invalid small-tier result.
- **Repair:** asking the model to fix its own invalid JSON, given the validation error.
- **Lift:** (recent-window rate + 0.01) / (baseline rate + 0.01). Above 1 means the topic is rising.
- **Gap score:** demand for a theme × how negative people are about competitors on that theme.
- **Roman Urdu:** Urdu written in Latin letters ("bohat mehenga hai"). Common in Pakistani posts and hard for small models.
