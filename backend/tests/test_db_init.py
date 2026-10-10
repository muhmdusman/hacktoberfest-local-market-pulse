"""Tests for app/db/init_db.py (requires the Postgres container)."""

from sqlalchemy import MetaData, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

import app.db.init_db as init_db_module
from app.db.base import NAMING_CONVENTION
from app.db.init_db import init_db
from app.db.session import engine

PROBE_TABLE = "init_db_probe"


class _ProbeBase(DeclarativeBase):
    """Isolated base so the probe table never leaks into the real Base.metadata."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class _Probe(_ProbeBase):
    __tablename__ = PROBE_TABLE
    id: Mapped[int] = mapped_column(primary_key=True)


async def test_init_db_creates_tables_with_named_constraints(monkeypatch):
    monkeypatch.setattr(init_db_module, "Base", _ProbeBase)
    try:
        await init_db(engine)
        async with engine.connect() as conn:
            tables = await conn.run_sync(lambda c: inspect(c).get_table_names())
            pk = await conn.run_sync(lambda c: inspect(c).get_pk_constraint(PROBE_TABLE))
        assert PROBE_TABLE in tables
        assert pk["name"] == f"pk_{PROBE_TABLE}"
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(_ProbeBase.metadata.drop_all)


async def test_init_db_is_idempotent_with_real_base():
    await init_db(engine)
    await init_db(engine)  # second run must not raise
