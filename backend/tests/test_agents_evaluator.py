"""Tests for app/agents/evaluator.py"""

import pytest

from app.agents.evaluator import MAX_ATTEMPTS, evaluate_hit, make_evaluator
from tests.fakes import DEFAULT_INSIGHT, AuthenticationError, FakeLLM

HIT = {"url": "https://a.example/1", "title": "Late night?", "snippet": "koi cafe khula hai?", "source": "web", "query": "q"}


async def test_valid_reply_on_first_try():
    out = await evaluate_hit(FakeLLM(), HIT, "cafe", "Islamabad")
    assert out["status"] == "ok"
    assert out["insight"]["pain_points"] == DEFAULT_INSIGHT["pain_points"]
    assert (out["attempts"], out["repairs"], out["model"]) == (1, 0, "fake-7b")
    assert out["url"] == HIT["url"]


async def test_invalid_reply_is_repaired_with_the_error_quoted():
    llm = FakeLLM(bad_replies=1)
    out = await evaluate_hit(llm, HIT, "cafe", "Islamabad")
    assert out["status"] == "ok" and out["repairs"] == 1 and out["attempts"] == 2
    assert "That reply was invalid" in llm.calls[1][-1].content


async def test_always_invalid_marks_failed():
    out = await evaluate_hit(FakeLLM(bad_replies=99), HIT, "cafe", "Islamabad")
    assert out["status"] == "failed" and out["insight"] is None
    assert out["attempts"] == MAX_ATTEMPTS and out["error"]


async def test_transient_provider_error_is_retried():
    llm = FakeLLM(error=RuntimeError("json_validate_failed"))
    out = await evaluate_hit(llm, HIT, "cafe", "Islamabad")
    assert out["status"] == "failed" and len(llm.calls) == MAX_ATTEMPTS


async def test_evaluator_keeps_order_and_bounds_concurrency():
    hits = [{**HIT, "url": f"https://a.example/{i}"} for i in range(5)]
    out = await make_evaluator(FakeLLM(), max_concurrency=2)({"hits": hits, "business": "cafe", "city": "Islamabad"})
    assert [e["url"] for e in out["evaluated"]] == [h["url"] for h in hits]


async def test_fatal_error_aborts_the_whole_stage():
    node = make_evaluator(FakeLLM(error=AuthenticationError("bad key")), max_concurrency=2)
    with pytest.raises(AuthenticationError):
        await node({"hits": [HIT, {**HIT, "url": "https://b.example"}], "business": "cafe", "city": "Islamabad"})
