"""Tests for app/tools/web_search.py"""

from app.tools import web_search as ws


async def test_web_search_tool_returns_digest_and_hits_artifact(fake_search):
    msg = await ws.web_search.ainvoke({"name": "web_search", "args": {"query": "cafe"}, "id": "1", "type": "tool_call"})
    assert msg.content.startswith("2 results")
    assert [h["source"] for h in msg.artifact] == ["web", "web"]
    assert msg.artifact[0]["query"] == "cafe"


async def test_reddit_search_prefixes_site_and_keeps_only_reddit(fake_search):
    msg = await ws.reddit_search.ainvoke({"name": "reddit_search", "args": {"query": "cafe"}, "id": "1", "type": "tool_call"})
    assert len(msg.artifact) == 2
    assert all(h["source"] == "reddit" for h in msg.artifact)
    assert msg.artifact[0]["query"] == "site:reddit.com cafe"


async def test_search_retries_with_backoff_then_succeeds(monkeypatch):
    calls, sleeps = [], []

    def flaky(query, max_results):
        calls.append(query)
        if len(calls) == 1:
            raise RuntimeError("Ratelimit")
        return [{"href": "https://a.example/x", "title": "T", "body": "B"}]

    async def no_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(ws, "_ddgs_text", flaky)
    monkeypatch.setattr(ws.asyncio, "sleep", no_sleep)
    hits = await ws.search("cafe")
    assert len(hits) == 1 and len(calls) == 2
    assert 1.0 <= sleeps[0] < 1.5  # base backoff + jitter


async def test_search_gives_up_with_empty_list(monkeypatch):
    async def no_sleep(_):
        return None

    def broken(query, max_results):
        raise RuntimeError("boom")

    monkeypatch.setattr(ws, "_ddgs_text", broken)
    monkeypatch.setattr(ws.asyncio, "sleep", no_sleep)
    assert await ws.search("cafe") == []


async def test_no_results_is_not_retried(monkeypatch):
    calls = []

    def empty(query, max_results):
        calls.append(query)
        raise RuntimeError("No results found.")

    monkeypatch.setattr(ws, "_ddgs_text", empty)
    assert await ws.search("cafe") == []
    assert len(calls) == 1


def test_normalize_drops_non_http_and_cleans_text():
    hits = ws._normalize(
        [{"href": "ftp://x"}, {"href": "https://www.reddit.com/r/a", "title": "  A \n B ", "body": None}], "q"
    )
    assert hits == [{"url": "https://www.reddit.com/r/a", "title": "A B", "snippet": "", "source": "reddit", "query": "q"}]


def test_is_reddit():
    assert ws.is_reddit("https://old.reddit.com/r/x")
    assert not ws.is_reddit("https://notreddit.com/r/x")
