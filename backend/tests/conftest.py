"""Shared pytest fixtures.

DB-backed tests need the Postgres container running:
    docker compose --env-file .env.local -f docker/docker-compose.local.yml up -d
"""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
async def _dispose_engine() -> AsyncIterator[None]:
    """pytest-asyncio uses a fresh event loop per test; drop pooled connections
    afterwards so asyncpg never reuses a connection bound to a closed loop."""
    yield
    await engine.dispose()


@pytest.fixture
def fake_search(monkeypatch):
    """Replace the ddgs network call with canned hits."""
    from app.tools import web_search as web_search_module
    from tests.fakes import fake_ddgs

    monkeypatch.setattr(web_search_module, "_ddgs_text", fake_ddgs)
    return fake_ddgs


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """HTTP client that calls the ASGI app in-process (no server needed)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class BrokenSession:
    """Stand-in for AsyncSession that fails like an unreachable database."""

    async def execute(self, *_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    async def close(self) -> None:
        return None
