"""Database bootstrap helpers used by the app lifespan."""

from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.models import Base


async def init_db(engine: AsyncEngine) -> None:
    """Create any tables registered on Base.metadata that don't exist yet."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
