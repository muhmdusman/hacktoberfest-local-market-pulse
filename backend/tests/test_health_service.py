"""Tests for app/services/health_service.py"""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.services.health_service import check_database
from tests.conftest import BrokenSession


async def test_check_database_true_when_postgres_up(db_session):
    assert await check_database(db_session) is True


async def test_check_database_false_on_sqlalchemy_error():
    assert await check_database(BrokenSession()) is False


async def test_check_database_false_when_server_unreachable():
    # Nothing listens on port 1, simulating a stopped container.
    dead_engine = create_async_engine(
        "postgresql+asyncpg://user:pwd@127.0.0.1:1/none",
        connect_args={"timeout": 3},
    )
    try:
        async with async_sessionmaker(dead_engine)() as session:
            assert await check_database(session) is False
    finally:
        await dead_engine.dispose()
