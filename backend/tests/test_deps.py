"""Tests for app/api/deps.py (requires the Postgres container)."""

from typing import get_args

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession, get_db


async def test_get_db_yields_working_async_session():
    gen = get_db()
    session = await anext(gen)
    try:
        assert isinstance(session, AsyncSession)
        assert (await session.execute(text("SELECT 1"))).scalar_one() == 1
    finally:
        await gen.aclose()


async def test_get_db_closes_session_when_request_ends():
    gen = get_db()
    session = await anext(gen)
    await session.execute(text("SELECT 1"))
    assert session.in_transaction()

    await gen.aclose()

    assert not session.in_transaction()


def test_db_session_alias_wires_get_db_dependency():
    session_type, depends = get_args(DbSession)
    assert session_type is AsyncSession
    assert depends.dependency is get_db
