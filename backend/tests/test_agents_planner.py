"""Tests for app/agents/planner.py"""

import pytest

from app.agents.planner import MAX_SEARCHES, fallback_searches, make_planner
from app.tools import TOOLS
from tests.fakes import AuthenticationError, FakeLLM

STATE = {"business": "cafe", "city": "Islamabad", "areas": ["F-7"], "competitors": ["Brew Bastion"], "sources": ["web", "reddit"]}


async def test_model_plan_becomes_tool_calls():
    out = await make_planner(FakeLLM(), TOOLS)(STATE)
    calls = out["messages"][0].tool_calls
    assert [c["name"] for c in calls] == ["web_search", "reddit_search"]
    assert calls[0]["args"] == {"query": "best cafe in Islamabad"}
    assert out["queries"][0] == {"tool": "web_search", "query": "best cafe in Islamabad"}


async def test_invalid_plan_falls_back_to_templates():
    out = await make_planner(FakeLLM(plan="not json at all"), TOOLS)(STATE)
    assert len(out["queries"]) == MAX_SEARCHES
    assert {q["tool"] for q in out["queries"]} == {"web_search", "reddit_search"}


async def test_disabled_source_tools_are_dropped_and_coverage_kept():
    plan = {"searches": [{"tool": "reddit_search", "query": "cafe islamabad"}, {"tool": "made_up", "query": "x y z"}]}
    out = await make_planner(FakeLLM(plan=plan), TOOLS)({**STATE, "sources": ["web"]})
    assert {q["tool"] for q in out["queries"]} == {"web_search"}


async def test_every_enabled_source_gets_a_search():
    plan = {"searches": [{"tool": "web_search", "query": "best cafe islamabad"}]}
    out = await make_planner(FakeLLM(plan=plan), TOOLS)(STATE)
    assert {q["tool"] for q in out["queries"]} == {"web_search", "reddit_search"}


async def test_fatal_provider_error_propagates():
    with pytest.raises(AuthenticationError):
        await make_planner(FakeLLM(error=AuthenticationError("bad key")), TOOLS)(STATE)


def test_fallback_includes_roman_urdu_area_and_competitor():
    queries = [s["query"] for s in fallback_searches(STATE, ["web_search"])]
    assert "acha cafe Islamabad kahan hai" in queries
    assert any("F-7" in q for q in queries)
    assert any("Brew Bastion" in q for q in queries)
