"""Strategist agent: aggregates evaluated results and writes this week's actions."""

import json
import logging
from collections import Counter
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.errors import is_fatal
from app.agents.jsonio import parse_json_object, reply_text
from app.agents.schemas import Actions
from app.agents.state import ScanState

log = logging.getLogger("agent.strategist")

TOP_N = 8

SYSTEM_PROMPT = """You are an SEO and marketing advisor for a small {business} in {city}.
From the research summary, write 3 specific actions for this week, one sentence each.
Each action must name the keyword, complaint or request it targets. Do not invent facts.
Reply with JSON only: {{"actions": ["...", "...", "..."]}}"""


def _top(counter: Counter) -> list[dict[str, Any]]:
    return [{"term": term, "count": count} for term, count in counter.most_common(TOP_N)]


def aggregate(evaluated: list[dict[str, Any]]) -> dict[str, Any]:
    """Count what customers said across all relevant, successfully evaluated results."""
    ok = [e for e in evaluated if e["status"] == "ok" and e.get("insight")]
    relevant = [e for e in ok if e["insight"]["relevant"]]

    sentiment: Counter = Counter()
    pains: Counter = Counter()
    requests: Counter = Counter()
    keywords: Counter = Counter()
    mentions: Counter = Counter()
    negative: Counter = Counter()
    names: dict[str, str] = {}
    questions: list[dict[str, Any]] = []

    for e in relevant:
        ins = e["insight"]
        sentiment[ins["sentiment"]] += 1
        pains.update(ins["pain_points"])
        requests.update(ins["requests"])
        keywords.update(ins["keywords"])
        for name in ins["competitors"]:
            key = name.lower()
            names.setdefault(key, name)
            mentions[key] += 1
            if ins["sentiment"] in ("neg", "mixed"):
                negative[key] += 1
        if ins["question"]:
            questions.append({"question": ins["question"], "url": e["url"], "title": e["title"], "source": e["source"]})

    return {
        "totals": {
            "results": len(evaluated),
            "evaluated": len(ok),
            "relevant": len(relevant),
            "failed": len(evaluated) - len(ok),
        },
        "sentiment": {k: sentiment.get(k, 0) for k in ("pos", "neg", "neutral", "mixed")},
        "pain_points": _top(pains),
        "requests": _top(requests),
        "keywords": _top(keywords),
        "competitors": [
            {
                "name": names[key],
                "mentions": count,
                "negative": negative[key],
                "negativity": round((negative[key] + 1) / (count + 2), 2),  # smoothed
            }
            for key, count in mentions.most_common(TOP_N)
        ],
        "questions": questions[:10],
        "threads_to_answer": [q for q in questions if q["source"] == "reddit"][:8],
    }


def fallback_actions(summary: dict[str, Any], business: str, city: str) -> list[str]:
    """Rule-based actions when the model reply is unusable."""
    actions = []
    if summary["requests"]:
        actions.append(f'Publish a page targeting "{summary["requests"][0]["term"]}", the top customer request for a {business} in {city}.')
    if summary["pain_points"]:
        actions.append(f'Fix and publicly address "{summary["pain_points"][0]["term"]}", the most common complaint.')
    if summary["questions"]:
        actions.append(f"Answer the {len(summary['questions'])} customer questions found in an FAQ on your site.")
    if summary["keywords"] and len(actions) < 3:
        actions.append(f'Use "{summary["keywords"][0]["term"]}" in your page titles and Google Business profile.')
    return actions or [f"Not enough relevant posts yet. Re-run with more areas or competitors in {city}."]


def make_strategist(llm: Any):
    async def strategist(state: ScanState) -> dict[str, Any]:
        business, city = state["business"], state["city"]
        summary = aggregate(state.get("evaluated", []))
        actions: list[str] = []

        if summary["totals"]["relevant"]:
            digest = {k: summary[k] for k in ("sentiment", "pain_points", "requests", "keywords", "competitors")}
            digest["questions"] = [q["question"] for q in summary["questions"][:5]]
            try:
                reply = await llm.bind(response_format={"type": "json_object"}).ainvoke(
                    [
                        SystemMessage(content=SYSTEM_PROMPT.format(business=business, city=city)),
                        HumanMessage(content="Research summary:\n" + json.dumps(digest, ensure_ascii=False)),
                    ]
                )
                actions = Actions.model_validate(parse_json_object(reply_text(reply))).actions
            except Exception as exc:
                if is_fatal(exc):
                    raise
                log.warning("model actions rejected (%s) · using rule-based actions", type(exc).__name__)

        origin = "model" if actions else "rules"
        summary["actions"] = actions or fallback_actions(summary, business, city)
        summary["actions_source"] = origin
        log.info("%d actions by %s · %d relevant of %d", len(summary["actions"]), origin, summary["totals"]["relevant"], summary["totals"]["results"])
        return {"summary": summary}

    return strategist
