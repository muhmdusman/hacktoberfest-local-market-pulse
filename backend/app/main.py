"""FastAPI application entrypoint. Run with: uv run uvicorn app.main:app --reload"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.init_db import init_db
from app.db.session import engine
from app.llm.factory import LLMNotConfiguredError, ensure_llm_ready
from app.llm.registry import ModelNotAllowedError

log = logging.getLogger("app")


def _model_banner() -> str:
    try:
        spec = ensure_llm_ready()
    except (LLMNotConfiguredError, ModelNotAllowedError) as exc:
        return f"LLM unavailable · {exc}"
    return f"{spec.id} · {spec.params_b}B · {spec.license} · via {spec.provider}"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Startup: fail fast if Postgres is unreachable and create any missing tables.
    await init_db(engine)
    log.info("ready · %s", _model_banner())
    yield
    # Shutdown: close pooled connections cleanly.
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
