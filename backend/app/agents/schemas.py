"""Pydantic contracts for model output. Every LLM reply is validated against one."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

_SENTIMENT_ALIASES = {"positive": "pos", "negative": "neg", "neu": "neutral", "mix": "mixed"}
MAX_LABELS = 6
_EMPTY = {"", "none", "null", "n/a", "na", "unknown", "nil"}
# Small models often tag the platform or poster as a "competitor".
_PLATFORMS = ("reddit", "tripadvisor", "google", "facebook", "instagram", "youtube", "yelp", "tiktok", "twitter", "foodpanda", "zomato")


def _as_labels(value: Any) -> list[str]:
    """Coerce a model value into a short, de-duplicated list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        raise ValueError("must be a list of strings")
    labels: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        label = " ".join(item.split()).strip(" .,;")
        if label.lower() not in _EMPTY and label.lower() not in (x.lower() for x in labels):
            labels.append(label)
    return labels[:MAX_LABELS]


def is_business_name(name: str) -> bool:
    """False for platforms, subreddits, usernames and URLs."""
    low = name.lower()
    if low.startswith(("r/", "u/", "@", "http", "www.")) or ".com" in low:
        return False
    return not any(p in low for p in _PLATFORMS)


class PlannedSearch(BaseModel):
    tool: str
    query: str = Field(min_length=3, max_length=120)


class SearchPlan(BaseModel):
    searches: list[PlannedSearch] = Field(min_length=1)


class Insight(BaseModel):
    """What the evaluator extracts from one search result."""

    relevant: bool
    sentiment: Literal["pos", "neg", "neutral", "mixed"]
    pain_points: list[str] = Field(default_factory=list)
    requests: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    question: str | None = None
    confidence: float = Field(ge=0, le=1)

    @field_validator("sentiment", mode="before")
    @classmethod
    def _sentiment(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip().lower()
            return _SENTIMENT_ALIASES.get(v, v)
        return v

    @field_validator("pain_points", "requests", "keywords", mode="before")
    @classmethod
    def _lower_labels(cls, v: Any) -> list[str]:
        return [label.lower() for label in _as_labels(v)]

    @field_validator("competitors", mode="before")
    @classmethod
    def _names(cls, v: Any) -> list[str]:
        return [name for name in _as_labels(v) if is_business_name(name)]

    @field_validator("question", mode="before")
    @classmethod
    def _question(cls, v: Any) -> str | None:
        if not isinstance(v, str) or v.strip().lower() in ("", "null", "none"):
            return None
        return v.strip()

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and 1 < v <= 100:  # "85" means 85%
            return v / 100
        return v


class Actions(BaseModel):
    actions: list[str] = Field(min_length=1, max_length=5)
