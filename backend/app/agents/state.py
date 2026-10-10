"""Shared state that flows through the scan graph."""

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class ScanState(TypedDict, total=False):
    # Input brief
    scan_id: str
    business: str
    city: str
    areas: list[str]
    competitors: list[str]
    sources: list[str]
    max_results: int
    # Planner <-> tools transcript (AIMessage with tool_calls, then ToolMessages)
    messages: Annotated[list[AnyMessage], add_messages]
    # Stage outputs
    queries: list[dict[str, str]]  # planner: [{"tool", "query"}]
    hits: list[dict[str, Any]]  # collector: deduped, balanced search results
    evaluated: list[dict[str, Any]]  # evaluator: hit + insight + trace
    summary: dict[str, Any]  # strategist: aggregates + actions


def initial_state(scan: Any) -> ScanState:
    """Build the graph input from a Scan row (or any object with the same attributes)."""
    return {
        "scan_id": str(scan.id),
        "business": scan.business,
        "city": scan.city,
        "areas": list(scan.areas or []),
        "competitors": list(scan.competitors or []),
        "sources": list(scan.sources or []),
        "max_results": scan.max_results,
        "messages": [],
        "queries": [],
        "hits": [],
        "evaluated": [],
        "summary": {},
    }
