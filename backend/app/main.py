"""FastAPI application entrypoint. Run with: uv run uvicorn app.main:app --reload"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.db.init_db import init_db
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Startup: fail fast if Postgres is unreachable and create any missing tables.
    await init_db(engine)
    yield
    # Shutdown: close pooled connections cleanly.
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
