"""Tests for app/core/logging.py"""

import logging

from rich.logging import RichHandler

from app.core import logging as app_logging


def test_setup_is_idempotent_and_routes_uvicorn_to_root(monkeypatch):
    monkeypatch.setattr(app_logging, "_configured", False)
    app_logging.setup_logging("INFO")
    app_logging.setup_logging("DEBUG")  # second call is a no-op

    root = logging.getLogger()
    rich_handlers = [h for h in root.handlers if isinstance(h, RichHandler)]
    assert len(rich_handlers) == 1
    assert root.level == logging.INFO
    assert logging.getLogger("uvicorn.access").propagate is True
    assert logging.getLogger("httpx").level == logging.WARNING


def test_short_names_for_uvicorn_loggers():
    record = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, "GET /", None, None)
    app_logging._ShortName().filter(record)
    assert record.short == "http"
