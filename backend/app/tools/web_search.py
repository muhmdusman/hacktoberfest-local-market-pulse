"""Search tools for the planner agent, backed by `ddgs` metasearch (no API key).

Reddit's anonymous JSON API is blocked and its official API needs manual
approval, so Reddit threads are discovered with `site:reddit.com` web search,
the same fallback Agent-Reach (MIT) documents for its Exa route.

Tools never raise: failures are retried with exponential backoff + jitter and
then degrade to an empty result, so one bad query can't sink a scan.
"""

import asyncio
import logging
import random
from typing import Any
from urllib.parse import urlparse

from ddgs import DDGS
from langchain_core.tools import tool

log = logging.getLogger("tools.search")

RESULTS_PER_QUERY = 8
MAX_ATTEMPTS = 3
RETRY_BASE_S = 1.0  # backoff: 1s, 2s (+ jitter)


def _ddgs_text(query: str, max_results: int) -> list[dict[str, Any]]:
    """Blocking ddgs call; executed in a worker thread."""
    return DDGS(timeout=10).text(query, max_results=max_results) or []


def is_reddit(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in ("reddit.com", "redd.it") or host.endswith(".reddit.com")


def _clean(text: Any, limit: int) -> str:
    return " ".join(str(text or "").split())[:limit]


def _normalize(raw: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    hits = []
    for item in raw:
        url = str(item.get("href") or item.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            continue
        hits.append(
            {
                "url": url,
                "title": _clean(item.get("title"), 200),
                "snippet": _clean(item.get("body"), 600),
                "source": "reddit" if is_reddit(url) else "web",
                "query": query,
            }
        )
    return hits


async def search(query: str, max_results: int = RESULTS_PER_QUERY) -> list[dict[str, Any]]:
    """Run one search with retries. Returns normalised hits, never raises."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            raw = await asyncio.to_thread(_ddgs_text, query, max_results)
            return _normalize(raw, query)
        except Exception as exc:  # ddgs raises DDGSException / Ratelimit / Timeout
            if "no results" in str(exc).lower():
                return []
            if attempt == MAX_ATTEMPTS:
                log.warning("gave up after %d tries · %s · %s", attempt, query, type(exc).__name__)
                return []
            delay = RETRY_BASE_S * 2 ** (attempt - 1) + random.uniform(0, RETRY_BASE_S / 2)
            log.warning("retry %d in %.1fs · %s · %s", attempt, delay, query, type(exc).__name__)
            await asyncio.sleep(delay)
    return []


def _digest(hits: list[dict[str, Any]]) -> str:
    """Short text the model sees; the full hits travel as the tool artifact."""
    titles = "; ".join(h["title"][:60] for h in hits[:5])
    return f"{len(hits)} results. {titles}".strip()


@tool(response_format="content_and_artifact")
async def web_search(query: str) -> tuple[str, list[dict[str, Any]]]:
    """Search the public web (reviews, blogs, listicles, news) for what customers say about local businesses."""
    hits = await search(query)
    log.info("web_search · %s · %d hits", query, len(hits))
    return _digest(hits), hits


@tool(response_format="content_and_artifact")
async def reddit_search(query: str) -> tuple[str, list[dict[str, Any]]]:
    """Search Reddit threads for honest customer opinions, complaints and unanswered questions."""
    hits = [h for h in await search(f"site:reddit.com {query}") if h["source"] == "reddit"]
    log.info("reddit_search · %s · %d hits", query, len(hits))
    return _digest(hits), hits
