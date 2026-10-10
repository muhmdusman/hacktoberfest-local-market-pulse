"""Evaluator agent: the open-weight model scores every search result.

Per result: JSON-mode extraction -> pydantic validation -> up to 2 repair
prompts quoting the validation error -> 'failed' if still invalid.
Transient provider errors (429/5xx) are already retried with exponential
backoff by the client (LLM_MAX_RETRIES). Results run concurrently, bounded
by LLM_MAX_CONCURRENCY, and keep their input order.
"""

import asyncio
import logging
import time
from statistics import median
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.errors import is_fatal
from app.agents.jsonio import parse_json_object, reply_text
from app.agents.schemas import Insight
from app.agents.state import ScanState
from app.core.config import get_settings

log = logging.getLogger("agent.evaluator")

MAX_ATTEMPTS = 3  # first try + 2 repairs

SYSTEM_PROMPT = """You analyse ONE search result for a {business} market study in {city}.
Return JSON only, with exactly these keys:
{{"relevant": true, "sentiment": "neg", "pain_points": [], "requests": [], "competitors": [], "keywords": [], "question": null, "confidence": 0.8}}
- relevant: true only if the text is about {business} places in or near {city}.
- sentiment: one of "pos", "neg", "neutral", "mixed".
- pain_points: short English complaint labels, e.g. "slow service", "high prices", "no backup power".
- requests: features or services customers want, e.g. "late-night hours", "quiet place to work". Not search phrases.
- competitors: names of specific {business} places or shops mentioned. Never websites, platforms (Reddit, Tripadvisor) or usernames.
- keywords: phrases locals would search for, lowercase, e.g. "quiet cafe f-7".
- question: the customer's question from the title or text (a title ending in "?" counts), else null.
- confidence: 0 to 1.
Text can be English, Urdu or Roman Urdu ("bohat mehenga" = "very expensive"); always write labels in English. Use only facts in the text."""

REPAIR_PROMPT = "That reply was invalid: {error}. Return only the corrected JSON object."


def _short(exc: BaseException) -> str:
    return " ".join(str(exc).split())[:240]


def model_name(llm: Any) -> str:
    return getattr(llm, "model_name", None) or getattr(llm, "model", None) or "unknown"


async def evaluate_hit(llm: Any, hit: dict[str, Any], business: str, city: str) -> dict[str, Any]:
    """Extract an Insight from one hit. Returns the hit plus insight and trace."""
    messages: list[Any] = [
        SystemMessage(content=SYSTEM_PROMPT.format(business=business, city=city)),
        HumanMessage(content=f"Source: {hit['source']}\nTitle: {hit['title']}\nText: {hit['snippet'] or '(no text)'}"),
    ]
    json_llm = llm.bind(response_format={"type": "json_object"})
    started, repairs, error = time.perf_counter(), 0, None
    insight: dict[str, Any] | None = None
    attempt = 0

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            reply = await json_llm.ainvoke(messages)
        except Exception as exc:
            if is_fatal(exc):
                raise
            error = _short(exc)  # e.g. Groq json_validate_failed; try again as-is
            continue
        try:
            insight = Insight.model_validate(parse_json_object(reply_text(reply))).model_dump()
            break
        except ValueError as exc:  # JSONDecodeError and pydantic ValidationError
            error = _short(exc)
            if attempt < MAX_ATTEMPTS:
                repairs += 1
                messages = [
                    *messages,
                    AIMessage(content=reply_text(reply)),
                    HumanMessage(content=REPAIR_PROMPT.format(error=error)),
                ]

    return {
        **hit,
        "status": "ok" if insight else "failed",
        "insight": insight,
        "attempts": attempt,
        "repairs": repairs,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "model": model_name(llm),
        "error": None if insight else error,
    }


def make_evaluator(llm: Any, max_concurrency: int | None = None):
    async def evaluator(state: ScanState) -> dict[str, Any]:
        hits = state.get("hits", [])
        limit = asyncio.Semaphore(max_concurrency or get_settings().llm_max_concurrency)

        async def bounded(hit: dict[str, Any]) -> dict[str, Any]:
            async with limit:
                return await evaluate_hit(llm, hit, state["business"], state["city"])

        try:  # TaskGroup cancels the rest on a fatal error (bad key, retired model)
            async with asyncio.TaskGroup() as group:
                tasks = [group.create_task(bounded(h)) for h in hits]
        except ExceptionGroup as eg:
            raise eg.exceptions[0] from None
        evaluated = [t.result() for t in tasks]

        ok = [e for e in evaluated if e["status"] == "ok"]
        log.info(
            "%d/%d evaluated · %d relevant · %d repairs · p50 %d ms",
            len(ok),
            len(evaluated),
            sum(1 for e in ok if e["insight"]["relevant"]),
            sum(e["repairs"] for e in evaluated),
            median(e["latency_ms"] for e in evaluated) if evaluated else 0,
        )
        return {"evaluated": evaluated}

    return evaluator
