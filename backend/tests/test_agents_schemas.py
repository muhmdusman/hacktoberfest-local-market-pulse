"""Tests for app/agents/schemas.py"""

import pytest
from pydantic import ValidationError

from app.agents.schemas import Insight, is_business_name


def test_insight_normalises_model_quirks():
    insight = Insight.model_validate(
        {
            "relevant": True,
            "sentiment": "Negative",
            "pain_points": ["Slow Service", "slow service", "none"],
            "requests": "late-night hours",
            "competitors": ["Brew Bastion", "Tripadvisor", "r/islamabad - Reddit", "u/someone", "null"],
            "keywords": [],
            "question": "null",
            "confidence": 85,
            "extra": "ignored",
        }
    )
    assert insight.sentiment == "neg"
    assert insight.pain_points == ["slow service"]
    assert insight.requests == ["late-night hours"]
    assert insight.competitors == ["Brew Bastion"]
    assert insight.question is None
    assert insight.confidence == 0.85


@pytest.mark.parametrize(
    "bad", [{"sentiment": "angry"}, {"confidence": 150}, {"relevant": "maybe"}]
)
def test_insight_rejects_invalid_values(bad):
    data = {"relevant": True, "sentiment": "pos", "confidence": 0.5, **bad}
    with pytest.raises(ValidationError):
        Insight.model_validate(data)


def test_is_business_name():
    assert is_business_name("Kahwa House")
    for not_a_business in ("Google Maps", "www.cafe.example", "u/abc", "foo.com"):
        assert not is_business_name(not_a_business)
