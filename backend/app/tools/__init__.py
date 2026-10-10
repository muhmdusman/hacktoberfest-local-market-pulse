"""Tools the agents can call. Each source the user enables maps to one tool."""

from app.tools.web_search import reddit_search, web_search

TOOLS = [web_search, reddit_search]
SOURCE_TOOLS = {"web": "web_search", "reddit": "reddit_search"}

__all__ = ["SOURCE_TOOLS", "TOOLS", "reddit_search", "web_search"]
