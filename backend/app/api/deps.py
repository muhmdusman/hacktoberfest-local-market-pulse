"""Shared FastAPI dependencies injected into route handlers."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield one AsyncSession per request; it is closed automatically afterwards."""
    async with AsyncSessionLocal() as session:
        yield session


# Use as a parameter type in routes: `async def handler(db: DbSession): ...`
DbSession = Annotated[AsyncSession, Depends(get_db)]
