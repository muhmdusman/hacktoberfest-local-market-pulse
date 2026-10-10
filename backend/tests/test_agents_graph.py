"""Tests for app/agents/graph.py and app/agents/state.py (full graph, fake LLM + search)."""

from types import SimpleNamespace

from app.agents.graph import NODES, build_scan_graph
from app.agents.state import initial_state

SCAN = SimpleNamespace(
    id="s1", business="cafe", city="Islamabad", areas=[], competitors=[], sources=["web", "reddit"], max_results=3
)


def test_initial_state_from_scan():
    state = initial_state(SCAN)
    assert state["scan_id"] == "s1" and state["sources"] == ["web", "reddit"] and state["messages"] == []


async def test_graph_runs_every_node_in_order(fake_search):
    from tests.fakes import FakeLLM

    graph = build_scan_graph(FakeLLM())
    order = []
    final = {}
    async for mode, chunk in graph.astream(initial_state(SCAN), stream_mode=["updates", "values"]):
        if mode == "updates":
            order.extend(chunk)
        else:
            final = chunk
    assert tuple(order) == NODES
    assert len(final["evaluated"]) == 3  # capped by max_results
    assert {e["source"] for e in final["evaluated"]} == {"web", "reddit"}
    assert final["summary"]["actions_source"] == "model"
