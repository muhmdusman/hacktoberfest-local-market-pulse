"""Tests for app/agents/collector.py"""

from langchain_core.messages import AIMessage, ToolMessage

from app.agents.collector import collect, url_key


def _hit(url, source):
    return {"url": url, "title": "t", "snippet": "s", "source": source, "query": "q"}


def test_dedupes_balances_sources_and_caps():
    web = [_hit(f"https://a.example/{i}", "web") for i in range(4)]
    reddit = [_hit(f"https://www.reddit.com/r/x/{i}", "reddit") for i in range(2)]
    dupe = [_hit("https://www.a.example/0/", "web")]
    messages = [
        AIMessage(content="", tool_calls=[]),
        ToolMessage(content="", tool_call_id="1", artifact=web + dupe),
        ToolMessage(content="", tool_call_id="2", artifact=reddit),
        ToolMessage(content="Error: boom", tool_call_id="3", status="error"),
    ]
    hits = collect({"messages": messages, "max_results": 4})["hits"]
    assert [h["source"] for h in hits] == ["web", "reddit", "web", "reddit"]
    assert len({url_key(h["url"]) for h in hits}) == 4


def test_url_key_ignores_www_trailing_slash_and_query():
    assert url_key("https://www.Example.com/Path/?a=1") == url_key("https://example.com/path")
