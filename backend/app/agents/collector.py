"""Collector: merges tool outputs into one deduplicated, source-balanced list."""

import logging
from itertools import zip_longest
from typing import Any
from urllib.parse import urlparse

from langchain_core.messages import ToolMessage

from app.agents.state import ScanState

log = logging.getLogger("agent.collector")


def url_key(url: str) -> str:
    """Identity of a page: host without www, path without trailing slash, no query."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    return f"{host}{parsed.path.rstrip('/').lower()}"


def collect(state: ScanState) -> dict[str, Any]:
    by_source: dict[str, list[dict[str, Any]]] = {}
    seen: set[str] = set()
    for msg in state.get("messages", []):
        # Successful tool calls carry their hits as the artifact; errors carry none.
        if not isinstance(msg, ToolMessage) or not isinstance(msg.artifact, list):
            continue
        for hit in msg.artifact:
            key = url_key(hit["url"])
            if key not in seen:
                seen.add(key)
                by_source.setdefault(hit["source"], []).append(hit)

    # Round-robin across sources so neither Reddit nor web crowds the other out.
    mixed = [h for group in zip_longest(*by_source.values()) for h in group if h is not None]
    hits = mixed[: state.get("max_results", 20)]
    found = " · ".join(f"{src} {len(items)}" for src, items in by_source.items()) or "nothing found"
    log.info("%d unique results kept · %s", len(hits), found)
    return {"hits": hits}
