# Build Plan — Local Market Pulse (150-minute build window)

Context and fixed decisions: [CONTEXT.md](CONTEXT.md). Rules: [../rules-hackathon.md](../rules-hackathon.md).

**Golden rule:** first get one complete flow working: `pulse run --cached` → report. Polish comes after. A small thing that works beats a big thing that doesn't.

## Timeline

| Time (min) | Milestone | Done when |
|---|---|---|
| 0–10 | Setup | `uv` env works, API credits claimed, `pulse models` lists ≤8B models |
| 10–85 | **Core flow (Phase A)** | `pulse run --cached --provider mock` writes `out/report.md` + `out/report.html` with all sections |
| 85–100 | Real model | Same run with the Groq key produces a real report. Cache it for the demo |
| 100–125 | Phase B: eval + Agent Skill + README | `pulse eval` table, skill validates, README has diagrams and test findings |
| 125–140 | Freeze | Tests green, secrets check, push, repo public, MLH form submitted |
| 140–150 | Demo rehearsal | 3-minute run-through (script below) |

## Roles (team of up to 3)

| Role | Owns | Phase A items | Phase B items |
|---|---|---|---|
| **A: Data** | collectors, normalization, demo snapshot, trends | 2, 3, 4, 7 (trends) | 12 (live web data), labels in `data/eval/` |
| **B: Harness** (lead) | registry, providers, router, extract, cache, metrics, CLI | 1, 5, 6, 8 | 9 (eval) |
| **C: Product & docs** | report, Agent Skill, README, diagrams, demo, MLH form | 7 (report) | 10, 11, submission |

Solo or pair: B's items first, then A's, then C's. Commit small and often to `main`. Pull before every push.

## Cut list (cut from the top when behind)

1. Self-consistency votes
2. HTML styling (Markdown report is enough)
3. Live collection (cached snapshot is enough for the demo)
4. Eval rows beyond `baseline` + `routed`

**Never cut:** 8B registry gate, repair + escalation, tests, README "built vs reused" section, SKILL.md, secrets hygiene.

## Fixed implementation decisions

1. **Env:** `uv venv --python 3.12 .venv` then `uv pip install --python .venv/bin/python -e '.[dev]'`. Build backend hatchling. Pins: `httpx==0.28.1`, `pydantic==2.11.7`, `python-dotenv==1.1.1`; dev `pytest==8.4.1` (if a pin fails, pin what uv resolves). CLI uses stdlib `argparse`.
2. **Commands:** TEST = `.venv/bin/python -m pytest -q`; RUN = `.venv/bin/pulse run --cached --provider mock`.
3. **Concurrency:** sync `httpx.Client` + `ThreadPoolExecutor` bounded by `LLM_MAX_CONCURRENCY` (default 4).
4. **Provider selection:** `--provider {mock,openai,ollama}` > env `LLM_PROVIDER` > `openai` if `LLM_API_KEY` set, else `mock`. Stdout and the report must say clearly when mock is used ("MockProvider: deterministic test stand-in, not a real model").
5. **Model registry & 8B cap.** Each entry has `id, provider, nominal_size ("8B"), params_b (exact), license, tier, open_weight`. Rule: **reject if the nominal size class is above 8B or the exact count is above 8.5B, or if the model isn't open-weight.** That accepts the 8B class the organizers name as eligible (Llama 3.1 8B = 8.03B) and rejects 9B+, 14B, 32B, 70B. Defaults:
   - Groq (`LLM_BASE_URL=https://api.groq.com/openai/v1`): `llama-3.1-8b-instant` (8B class, 8.03B, Llama 3.1 Community License) for both tiers. Small = compact prompt with a low `max_tokens`. Large = full few-shot prompt + self-consistency.
   - OpenRouter: small `meta-llama/llama-3.2-3b-instruct` (3.21B), large `qwen/qwen-2.5-7b-instruct` (7.61B, Apache-2.0).
   - Ollama: small `qwen3:1.7b` (2.03B), large `qwen3:4b` (4.02B), Apache-2.0.
   - Mock: `mock-small`, `mock-large`.
   - Overridable via `LLM_MODEL_SMALL` / `LLM_MODEL_LARGE`; ids must exist in the registry, else a clear error.
6. **Fictional competitors** in synthetic data ("Brew Bastion", "Chai Chowk", "Kahwa House", "Daily Grind ISB") so fake complaints never target real businesses. Synthetic URLs use the reserved `.example` TLD.
7. **Artifacts in `out/`:** `records.jsonl` (collect), `insights.jsonl` + `metrics.json` (analyze), `report.md` + `report.html` (report), `eval.md` + `eval.json` (eval). LLM cache in `.cache/llm/<sha256>.json`.
8. **Snapshot format:** line 1 is `{"_meta": {"synthetic": true|false, "description": "...", "created": "...", "business": "cafe", "city": "Islamabad"}}`, then raw posts `{id, source, url, title, text, created_at, author, area}`. Raw `author` exists only in snapshot input; normalized records keep only `author_hash`.
9. **Data-access commands** (as routed by Agent-Reach; see `../Agent-Reach/agent_reach/channels/{reddit,web,exa_search}.py` and `agent_reach/skill/references/{social,search,web}.md`):
   - Reddit: `rdt search "<q>" --limit N`, `rdt read POST_ID` (try `--json`; if it fails, fall through). Never run `rdt login`, never read cookies.
   - Search: `mcporter call exa.web_search_exa query="<q>" numResults=N` (Reddit fallback: `query="site:reddit.com <q>"`). Parse JSON, else regex the `Title:`/`URL:`/`Text:` blocks.
   - Page text: GET `https://r.jina.ai/<URL>`, `Accept: text/plain`, 30 s timeout, 5 MB cap, detect anti-bot pages ("Just a moment...", "Attention Required! | Cloudflare").
   - `--urls FILE` (one URL per line) = a live web path that needs only Jina.
   - Fallback chain is always: tool → next tool → cached snapshot, with a clear message and install hint.
10. **Gap score:** `gap = demand × negativity`. demand = records whose requests or pain_points contain the theme. negativity = `(neg_or_mixed + 1) / (n + 2)` over records mentioning a competitor AND the theme (0.5 with no evidence).
11. **Trend windows** are relative to the newest `created_at`: recent = last 30 days, baseline = older. `lift = (recent_rate + 0.01) / (baseline_rate + 0.01)`, z = two-proportion z-score, opportunity = frequency × lift.
12. **FAQ JSON-LD** answers are placeholders ("Draft your answer here — verify facts before publishing"). The model never invents business facts.

## Task checklist

### Phase A: core flow

- [ ] **1. Scaffold** (B, ~8 min). `pyproject.toml` (name `local-market-pulse`, `requires-python>=3.12`, script `pulse = "pulse.cli:main"`, hatch `packages=["pulse"]`, pytest `testpaths=["tests"]`). `.gitignore`: `.env .venv/ out/ .cache/ __pycache__/ *.pyc .pytest_cache/ .agents/`. `.env.example` placeholders only: `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_API_KEY=your-key-here`, `LLM_MODEL_SMALL`, `LLM_MODEL_LARGE`, `OLLAMA_BASE_URL`, `LLM_MAX_CONCURRENCY`, `LLM_TIMEOUT_S`, `PULSE_CONFIDENCE_THRESHOLD`. `pulse/config.py` loads `.env` into a frozen `Settings`. **Keep the existing `LICENSE` unchanged.**
  Verify: `.venv/bin/python -c "import pulse, httpx, pydantic, dotenv"`.
- [ ] **2. Schemas, lexicon, normalization** (A, ~10 min). `pulse/schema.py`: `Record`, `Insight` (`extra="forbid"`, confidence 0–1), `ContentBrief` (outline ≥3), `AnalyzedRecord` (status ok / filtered / failed). `pulse/lexicon.py`: café keywords, Islamabad area tokens (F-6, F-7, F-10, G-9, G-11, E-7, Blue Area, Jinnah Super, Centaurus, Giga Mall…), ~60 Roman-Urdu words, EN + Roman-Urdu sentiment lexicon, pain-point synonym map → canonical labels, `canonicalize()`. `pulse/normalize.py`: `scrub_pii` (emails, `+92 3xx…`, `0092…`, `03xx-xxxxxxx`, long digit runs), `hash_author` (sha256), `normalize`, `dedupe` (url + normalized-text hash).
  Verify: `tests/test_normalize.py`.
- [ ] **3. Demo snapshot** (A, ~10 min). `data/snapshots/demo_islamabad_cafes.jsonl`: `_meta` with `synthetic: true` + ~80 posts over ~90 days (≥25 in the newest 30). Language mix: ~55% English, ~30% Roman Urdu / code-mixed, ~15% Urdu script. Source mix: ~55% Reddit, ~45% web. Include competitor complaints, requests, ~15 questions, ~8 off-topic posts, 3–4 fake PII strings, 2 near-duplicates. Recent-window trends to seed: late-night hours, no backup power (load shedding), sugar-free options. Baseline trends: high prices, slow service.
- [ ] **4. Collectors** (A, ~10 min). `pulse/collectors/{base,snapshot,reddit,web}.py` per decision 9. Subprocess with list argv (no shell), `shutil.which` checks, `--cached` (default) / `--live`. Docstring credits Agent-Reach.
  Verify: `tests/test_collectors.py` (missing tools → snapshot fallback + install hint; Exa text parser; anti-bot detection).
- [ ] **5. Harness core** (B, ~15 min). `pulse/harness/registry.py` (decision 5, `ModelTooLargeError`, `resolve_tiers`), `providers.py` (OpenAI-compatible with a `response_format` json_object attempt, Ollama `format=json`, retries with backoff + jitter on 429/5xx/timeout, semaphore), `mock.py` (deterministic, lexicon-based; knobs `invalid_json_first_n`, `small_low_confidence_on_mixed`), `cache.py`, `metrics.py` (calls per tier, cache hits, escalations, schema failures, repairs, tokens, p50/p95).
  Verify: `tests/test_registry.py` (70B, 14B, 9B rejected; 8B class + 7.61B accepted; closed model rejected; unknown id error), `tests/test_providers.py` (503 then success via `httpx.MockTransport`).
- [ ] **6. Router + extraction** (B, ~15 min, the centerpiece). `router.py`: `detect_lang` (Urdu script ratio ≥0.3 → `ur`; Roman-Urdu token ratio thresholds → `ur-Latn` / `mixed`; else `en`), `prefilter`, `route` (large tier for ur / ur-Latn / mixed / >800 chars / mixed-sentiment lexicon hits). `extract.py`: prompt (JSON-only, field definitions, canonical label list, one Roman-Urdu few-shot) → parse (strip fences, first balanced `{}`) → validate → ≤2 repair prompts → escalate → `failed`. Self-consistency on borderline confidence. Canonicalize labels. Shared `generate_json()` reused for briefs. Parallel `analyze()` with stable order.
  Verify: `tests/test_router.py`, `tests/test_extract.py` (Roman Urdu → large; junk filtered; repairs==1; escalated; always-invalid → failed; second run hits cache).
- [ ] **7. Trends + report** (A trends, C report, ~12 min). `pulse/trends.py` (decisions 10–11). `pulse/report.py`: 3–5 `ContentBrief`s via the large tier. Render `report.md` + standalone `report.html` (inline CSS, `html.escape` everything, JSON-LD via `json.dumps`). Sections: header (provenance + SYNTHETIC banner, models with size/license/provider, mock disclaimer), keyword opportunities, FAQ + JSON-LD, content briefs, competitor gaps, Reddit threads worth answering + honest-participation note, harness metrics.
  Verify: `tests/test_trends.py` (3/10 recent vs 1/20 baseline → lift ≈ 5.17), `tests/test_report.py` (escapes `<script>`, JSON-LD parses).
- [ ] **8. CLI + end-to-end** (B, ~5 min). `pulse collect | analyze | report | run | eval | models`, defaults: cafe, Islamabad, fictional competitors, reddit+web, `--cached`. Print a summary.
  Verify: `tests/test_e2e.py` + RUN finishes in <30 s. **CHECKPOINT: the demo works.**

### Phase B: real model, eval, skill, docs

- [ ] **8b. Real-model smoke run** (B, ~10 min, needs the key). Put the Groq key in `.env` (never commit it). Run `pulse models` and `pulse run --cached`. Check the report reads well, tune prompts if needed. Keep `.cache/llm/` so the demo replays instantly.
- [ ] **9. Eval** (B, ~12 min). `data/eval/label_template.jsonl`, `data/eval/seed_eval.jsonl` (~30 items, `label_status: "provisional — verify by hand"`). `pulse/eval.py`: systems `baseline` (lexicon only), `small-only`, `large-only`, `routed`. Metrics: relevance F1, sentiment accuracy + macro-F1, pain-point precision/recall, latency per item, escalation rate, calls. Writes `out/eval.md` + `out/eval.json`.
  Verify: `tests/test_eval.py`.
- [ ] **10. Agent Skill** (C, ~12 min), per [agentskills.io/specification](https://agentskills.io/specification). `skills/local-market-pulse/SKILL.md`. Frontmatter: `name: local-market-pulse` (= folder name), `description` (≤1024 chars: what + when + keywords), `license: MIT`, `compatibility` (≤500 chars), `metadata` (string → string). Body <500 lines: when to use, steps, worked example, edge cases. Supporting files: `scripts/run_pulse.sh`, `references/{HARNESS,DATA_SOURCES,REPORT_FORMAT}.md`, `assets/example_report.md`. Also add `pulse/__main__.py`.
  Verify: `uvx --from skills-ref skills-ref validate skills/local-market-pulse`, plus `tests/test_skill_spec.py` (local rule check).
- [ ] **11. README** (C, ~10 min). Project name + one-liner; domain; target user; problem; solution and core features. AI component: exact model name, parameter size, runtime/provider, what it does, ≤8B enforcement. Mermaid **architecture**, **data-flow** and **sequence** diagrams. "What we built vs. what we reused". Setup (deps, install, env var names, run, minimal example). Demo output. **Testing & findings** table (scenario, input, expected, actual, pass/fail), eval results, known limitations. Responsible use. Team names + contributions. License. Acknowledgements (Agent-Reach, rdt-cli, Exa, Jina, Meta Llama, Qwen, Groq). Also disclose the AI-assisted development tools we used.
- [ ] **12. Optional real web data** (A, ≤10 min). `pulse collect --live --sources web --urls urls.txt` with 3–5 public Islamabad café review pages. Save as `data/snapshots/live_web_<date>.jsonl` with `synthetic: false`.

## Freeze checklist (minute 125)

- [ ] `pytest -q` green; `pulse run` and `pulse eval` work from a clean clone
- [ ] `git check-ignore .env` prints `.env`; no keys found by `grep -rEn "gsk_|sk-[A-Za-z0-9]{20,}" --exclude-dir=.venv .`
- [ ] README renders on GitHub (Mermaid diagrams show), LICENSE present, repo **public**
- [ ] MLH form: title, description (problem, product, main feature, AI used), GitHub URL
- [ ] Team names and contributions in README

## Demo script (3 minutes)

1. **Problem (20 s):** Islamabad cafés can't afford $100/month listening tools, and Reddit threads shape both Google and AI answers.
2. **Run (60 s):** `pulse models` (only ≤8B open-weight models; a 70B entry is rejected), then `pulse run`. Point out Roman-Urdu posts routed to the large tier, repairs, escalations.
3. **Report (60 s):** rising keyword ("late night cafe F-7"), FAQ + JSON-LD, one content brief, competitor gap, Reddit threads worth answering.
4. **Proof (30 s):** `pulse eval` table, routed vs. baseline vs. single tier.
5. **Close (10 s):** open-source MIT, Agent Skill for any agent. Roadmap: more platforms, Search Console link, site generator.
