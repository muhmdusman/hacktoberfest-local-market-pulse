"""Deterministic stand-ins for the LLM and the search backend (no network, no key)."""

import json
from typing import Any

from langchain_core.messages import AIMessage

DEFAULT_PLAN = {
    "searches": [
        {"tool": "web_search", "query": "best cafe in Islamabad"},
        {"tool": "reddit_search", "query": "cafe Islamabad late night"},
    ]
}
DEFAULT_INSIGHT = {
    "relevant": True,
    "sentiment": "neg",
    "pain_points": ["slow service"],
    "requests": ["late-night hours"],
    "competitors": ["Brew Bastion"],
    "keywords": ["late night cafe f-7"],
    "question": "Any cafe open after midnight?",
    "confidence": 0.9,
}
DEFAULT_ACTIONS = {"actions": ["Publish a late-night page", "Fix slow service", "Answer the midnight question"]}


class FakeLLM:
    """Duck-typed LangChain chat model. Picks a reply by the agent's system prompt."""

    model_name = "fake-7b"

    def __init__(self, plan=None, insight=None, actions=None, bad_replies: int = 0, error: Exception | None = None):
        self.plan = DEFAULT_PLAN if plan is None else plan
        self.insight = DEFAULT_INSIGHT if insight is None else insight
        self.actions = DEFAULT_ACTIONS if actions is None else actions
        self.bad_replies = bad_replies  # evaluator: first N replies are invalid
        self.error = error  # raised on every call
        self.calls: list[list[Any]] = []

    def bind(self, **_kwargs):
        return self

    async def ainvoke(self, messages, **_kwargs):
        self.calls.append(messages)
        if self.error is not None:
            raise self.error
        system = messages[0].content
        if system.startswith("You are a market research planner"):
            return AIMessage(content=_dump(self.plan))
        if system.startswith("You analyse ONE search result"):
            if self.bad_replies > 0:
                self.bad_replies -= 1
                return AIMessage(content="Sure! Here is the analysis: relevant yes")
            return AIMessage(content=_dump(self.insight))
        if system.startswith("You are an SEO and marketing advisor"):
            return AIMessage(content=_dump(self.actions))
        raise AssertionError(f"unexpected prompt: {system[:60]}")


def _dump(value: Any) -> str:
    return value if isinstance(value, str) else json.dumps(value)


class AuthenticationError(Exception):
    """Same class name as the Groq SDK's, which is all is_fatal() checks."""


def fake_ddgs(query: str, max_results: int) -> list[dict[str, str]]:
    """Canned search backend: reddit hits for site:reddit.com queries, web hits otherwise."""
    slug = "-".join(query.lower().split())[:40]
    if query.startswith("site:reddit.com"):
        return [
            {"href": f"https://www.reddit.com/r/islamabad/comments/{slug}-{i}/", "title": f"Reddit thread {i}?", "body": "yaar koi acha cafe?"}
            for i in range(2)
        ]
    return [
        {"href": f"https://blog.example/{slug}-{i}", "title": f"Best cafes {i}", "body": "Brew Bastion is slow"}
        for i in range(2)
    ]
