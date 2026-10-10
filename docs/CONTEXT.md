# Project Context — Local Market Pulse

Read this first. It explains what we are building, why, and the decisions already made, so every teammate (and every AI coding assistant) works from the same picture. The step-by-step build plan is in [PLAN.md](PLAN.md). Event rules are in [../rules-hackathon.md](../rules-hackathon.md).

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
collect (Reddit + Web)  →  normalize & scrub PII  →  HARNESS (open-weight ≤8B models)
   →  trends & gap scoring  →  SEO action report (MD + HTML)  →  eval table
```

The report contains:

1. **Keyword opportunities**: local phrases ranked by frequency × recent lift.
2. **FAQ list**: real questions people ask, plus FAQPage JSON-LD for the SME's site.
3. **Content briefs** (written by the model): title, target keyword, outline, competitor weakness addressed.
4. **Competitor gap table**: complaints per competitor, plus demand nobody serves.
5. **Reddit threads worth answering**, with an honest-participation note (no auto-posting).
6. **Harness metrics**: models used, escalation rate, repairs, latency.

Out of scope today (roadmap slide only): more platforms (Facebook, X, YouTube, Google reviews), web UI, static-site generator, posting automation, connecting our earlier Search Console SEO tool.

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
| Orchestration | **Our own Python code.** No LangChain / LlamaIndex / DSPy / instructor / outlines. Only `httpx`, `pydantic`, `python-dotenv` (+ `pytest`) |
| Python | 3.12 via `uv` (system Python 3.14 is too new for some wheels) |
| Agent-Reach | Used as **credited reference/tooling** (MIT). We call the tools it routes to (`rdt`, `mcporter`+Exa, Jina Reader); we don't fork or copy it |
| Demo data | Cached snapshot so the demo works offline. If synthetic, it's labelled **SYNTHETIC DEMO DATA** everywhere and uses **fictional** competitor names |
| Reddit ethics | Report only lists threads worth answering. Humans answer, disclose affiliation, follow subreddit rules. Nothing posts automatically |
| Privacy | Usernames are SHA-256 hashed, emails and phone numbers scrubbed before any model call |
| Secrets | `.env` is git-ignored; only `.env.example` with placeholders is committed |

## Original work vs. reused (judges check this)

| Ours (original) | Reused (credited) |
|---|---|
| `pulse/harness/`: registry with 8B gate, providers (OpenAI-compatible, Ollama, Mock), router (Roman Urdu / Urdu script / code-mix detection, relevance pre-filter, tier routing), extraction loop (JSON schema validation → repair retries → escalation → self-consistency votes), result cache, run metrics | Agent-Reach: knowledge of which tool serves which platform |
| `pulse/trends.py`: lift, z-score, gap scoring | rdt-cli (Reddit), mcporter + Exa (search), Jina Reader (page → text) |
| `pulse/report.py`, `pulse/eval.py`, `pulse/cli.py`, collectors' fallback chain, PII scrubbing | Open-weight models (Meta Llama, Qwen), hosted runtime (Groq / OpenRouter / Ollama) |
| `skills/local-market-pulse/` Agent Skill, demo dataset, eval labels | httpx, pydantic, python-dotenv, pytest |

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
├── pyproject.toml  .env.example  .gitignore
├── pulse/
│   ├── cli.py config.py schema.py lexicon.py normalize.py trends.py report.py eval.py
│   ├── collectors/  base.py snapshot.py reddit.py web.py
│   └── harness/     registry.py providers.py mock.py router.py extract.py cache.py metrics.py
├── skills/local-market-pulse/  SKILL.md scripts/ references/ assets/
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
