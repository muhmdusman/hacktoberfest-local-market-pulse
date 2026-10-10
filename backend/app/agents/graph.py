"""The scan graph.

    START -> planner -> search (ToolNode) -> collector -> evaluator -> strategist -> END

planner    picks tools + queries (LLM, JSON mode)
search     executes the tool calls in parallel (LangGraph ToolNode, node-level retry)
collector  dedupes and balances sources (code)
evaluator  extracts an Insight per result (LLM, validate -> repair)
strategist aggregates and writes actions (code + LLM)
"""

from typing import Any

from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import RetryPolicy

from app.agents.collector import collect
from app.agents.evaluator import make_evaluator
from app.agents.planner import make_planner
from app.agents.state import ScanState
from app.agents.strategist import make_strategist
from app.tools import TOOLS

NODES = ("planner", "search", "collector", "evaluator", "strategist")


def build_scan_graph(llm: Any, tools: list[BaseTool] | None = None):
    tools = list(tools or TOOLS)
    builder = StateGraph(ScanState)
    builder.add_node("planner", make_planner(llm, tools))
    builder.add_node("search", ToolNode(tools), retry_policy=RetryPolicy(max_attempts=2))
    builder.add_node("collector", collect)
    builder.add_node("evaluator", make_evaluator(llm))
    builder.add_node("strategist", make_strategist(llm))
    for src, dst in zip((START, *NODES), (*NODES, END)):
        builder.add_edge(src, dst)
    return builder.compile()
