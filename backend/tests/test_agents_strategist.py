"""Tests for app/agents/strategist.py"""

from app.agents.strategist import aggregate, fallback_actions, make_strategist
from tests.fakes import DEFAULT_ACTIONS, DEFAULT_INSIGHT, FakeLLM


def _item(source="web", status="ok", **insight):
    return {
        "url": f"https://{source}.example/x",
        "title": "t",
        "source": source,
        "status": status,
        "insight": {**DEFAULT_INSIGHT, **insight} if status == "ok" else None,
    }


EVALUATED = [
    _item(),
    _item(source="reddit", sentiment="pos", competitors=["brew bastion"]),
    _item(relevant=False),
    _item(status="failed"),
]


def test_aggregate_counts_only_relevant_ok_results():
    s = aggregate(EVALUATED)
    assert s["totals"] == {"results": 4, "evaluated": 3, "relevant": 2, "failed": 1}
    assert s["sentiment"] == {"pos": 1, "neg": 1, "neutral": 0, "mixed": 0}
    assert s["pain_points"] == [{"term": "slow service", "count": 2}]
    assert s["competitors"] == [{"name": "Brew Bastion", "mentions": 2, "negative": 1, "negativity": 0.5}]
    assert len(s["questions"]) == 2 and len(s["threads_to_answer"]) == 1


async def test_strategist_uses_model_actions():
    out = await make_strategist(FakeLLM())({"evaluated": EVALUATED, "business": "cafe", "city": "Islamabad"})
    assert out["summary"]["actions"] == DEFAULT_ACTIONS["actions"]
    assert out["summary"]["actions_source"] == "model"


async def test_strategist_falls_back_to_rules_on_bad_reply():
    out = await make_strategist(FakeLLM(actions="nope"))({"evaluated": EVALUATED, "business": "cafe", "city": "Islamabad"})
    assert out["summary"]["actions_source"] == "rules"
    assert "late-night hours" in out["summary"]["actions"][0]


def test_fallback_actions_with_no_data():
    actions = fallback_actions(aggregate([]), "cafe", "Islamabad")
    assert len(actions) == 1 and "Not enough" in actions[0]
