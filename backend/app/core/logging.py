"""Console logging: one compact, colourised line per event.

    12:04:31 INFO     agent.planner  planned 5 searches
    12:04:33 INFO     tools.search   reddit_search · cafe islamabad · 7 hits
"""

import logging
import sys

from rich.console import Console
from rich.logging import RichHandler

# Display names for third-party loggers we route through the same handler.
_ALIASES = {"uvicorn": "server", "uvicorn.error": "server", "uvicorn.access": "http"}
# Libraries that are chatty at INFO; only their warnings are shown.
_QUIET = ("httpx", "httpcore", "groq", "primp", "ddgs", "asyncio", "langchain", "langgraph")

_configured = False


class _ShortName(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.short = _ALIASES.get(record.name, record.name)
        return True


def setup_logging(level: str = "INFO") -> None:
    """Install one Rich handler on the root logger. Safe to call more than once."""
    global _configured
    if _configured:
        return

    # A cp1252 pipe on Windows must never crash the app on Urdu text.
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(errors="replace")

    handler = RichHandler(
        console=Console(stderr=True),
        show_path=False,
        markup=False,
        rich_tracebacks=True,
        log_time_format="%H:%M:%S",
    )
    handler.addFilter(_ShortName())
    handler.setFormatter(logging.Formatter("%(short)-15s %(message)s"))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    for name in _ALIASES:  # uvicorn installs its own handlers; send them to ours
        uv_logger = logging.getLogger(name)
        uv_logger.handlers = []
        uv_logger.propagate = True
    for name in _QUIET:
        logging.getLogger(name).setLevel(logging.WARNING)

    _configured = True
