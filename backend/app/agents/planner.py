"""Planner agent: turns the business brief into search tool calls.

allam-2-7b (the <=8B chat model our Groq key serves) has no native function
calling, so the planner chooses tools in JSON mode. Its choices become standard
LangChain `tool_calls`, which LangGraph's ToolNode executes in parallel.
"""

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from pydantic import ValidationError

from app.agents.errors import is_fatal
from app.agents.jsonio import parse_json_object, reply_text
from app.agents.schemas import PlannedSearch
from app.agents.state import ScanState
from app.tools import SOURCE_TOOLS

log = logging.getLogger("agent.planner")

MAX_SEARCHES = 6

SYSTEM_PROMPT = """You are a market research planner for a small local business.
Choose search tools and write short queries (3-8 words) that surface what real customers say.

Tools:
{tools}

Cover complaints, "best {business} in <area>" lists, questions people ask, competitor names,
and at least one Roman Urdu query (for example "acha {business} {city} kahan hai").
Reply with JSON only: {{"searches": [{{"tool": "<tool name>", "query": "<query>"}}]}} with 4 to 6 items."""


def _brief(state: ScanState) -> str:
    lines = [f"Business type: {state['business']}", f"City: {state['city']}"]
    if state.get("areas"):
        lines.append("Areas: " + ", ".join(state["areas"]))
    if state.get("competitors"):
        lines.append("Competitors: " + ", ".join(state["competitors"]))
    return "\n".join(lines)


def fallback_searches(state: ScanState, tools: list[str]) -> list[dict[str, str]]:
    """Deterministic plan used when the model's plan is missing or invalid."""
    business, city = state["business"], state["city"]
    queries = [
        f"best {business} in {city}",
        f"{business} {city} complaints",
        f"acha {business} {city} kahan hai",
        f"{city} {business} recommendations",
    ]
    queries += [f"{business} {area} {city}" for area in state.get("areas", [])[:1]]
    queries += [f"{name} {city} review" for name in state.get("competitors", [])[:1]]
    return [{"tool": tools[i % len(tools)], "query": q} for i, q in enumerate(queries[:MAX_SEARCHES])]


def _parse_plan(reply: Any) -> list[dict[str, str]]:
    """Validate each planned search on its own so one bad item doesn't void the plan."""
    items = parse_json_object(reply_text(reply)).get("searches")
    if not isinstance(items, list):
        raise ValueError("'searches' must be a list")
    plan = []
    for item in items:
        try:
            plan.append(PlannedSearch.model_validate(item).model_dump())
        except ValidationError:
            continue
    return plan


def _finalize(searches: list[dict[str, str]], state: ScanState, allowed: list[str]) -> list[dict[str, str]]:
    """Dedupe, cap at MAX_SEARCHES, and guarantee every enabled source one search."""
    seen: set[tuple[str, str]] = set()
    plan = []
    for s in searches:
        key = (s["tool"], s["query"].lower())
        if s["tool"] in allowed and key not in seen:
            seen.add(key)
            plan.append(s)
    missing = [t for t in allowed if not any(s["tool"] == t for s in plan)]
    coverage = [{"tool": t, "query": f"{state['business']} {state['city']}"} for t in missing]
    return plan[: MAX_SEARCHES - len(coverage)] + coverage


def make_planner(llm: Any, tools: list[BaseTool]):
    descriptions = {t.name: t.description for t in tools}

    async def planner(state: ScanState) -> dict[str, Any]:
        allowed = [SOURCE_TOOLS[s] for s in state["sources"] if SOURCE_TOOLS.get(s) in descriptions]
        if not allowed:
            raise ValueError(f"No search tool available for sources {state['sources']}")

        system = SYSTEM_PROMPT.format(
            tools="\n".join(f"- {name}: {descriptions[name]}" for name in allowed),
            business=state["business"],
            city=state["city"],
        )
        searches: list[dict[str, str]] = []
        try:
            reply = await llm.bind(response_format={"type": "json_object"}).ainvoke(
                [SystemMessage(content=system), HumanMessage(content=_brief(state))]
            )
            searches = [s for s in _parse_plan(reply) if s["tool"] in allowed]
        except Exception as exc:
            if is_fatal(exc):
                raise
            log.warning("model plan rejected (%s) · using template queries", type(exc).__name__)

        origin = "model" if searches else "templates"
        plan = _finalize(searches or fallback_searches(state, allowed), state, allowed)
        calls = [
            {"name": s["tool"], "args": {"query": s["query"]}, "id": f"call_{i}", "type": "tool_call"}
            for i, s in enumerate(plan)
        ]
        log.info("%d searches planned by %s · %s", len(calls), origin, " | ".join(s["query"] for s in plan))
        return {"queries": plan, "messages": [AIMessage(content="", tool_calls=calls)]}

    return planner
