"""Tests for app/db/session.py (requires the Postgres container)."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine


def test_engine_uses_postgres_asyncpg_driver():
    assert engine.url.get_backend_name() == "postgresql"
    assert engine.dialect.driver == "asyncpg"


async def test_engine_connects_to_postgres_16_container():
    async with engine.connect() as conn:
        version = (await conn.execute(text("SHOW server_version"))).scalar_one()
    assert version.startswith("16")


async def test_engine_connects_to_configured_database():
    async with engine.connect() as conn:
        db_name = (await conn.execute(text("SELECT current_database()"))).scalar_one()
    assert db_name == engine.url.database


async def test_session_factory_yields_working_async_session():
    async with AsyncSessionLocal() as session:
        assert isinstance(session, AsyncSession)
        assert (await session.execute(text("SELECT 1"))).scalar_one() == 1


def test_session_factory_does_not_expire_on_commit():
    assert AsyncSessionLocal.kw["expire_on_commit"] is False
