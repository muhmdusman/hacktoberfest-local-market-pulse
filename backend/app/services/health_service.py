"""Health-check business logic, kept out of the route layer."""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def check_database(session: AsyncSession) -> bool:
    """Return True if Postgres answers a trivial query, False on any DB error."""
    try:
        result = await session.execute(text("SELECT 1"))
        return result.scalar_one() == 1
    except (SQLAlchemyError, OSError):
        # OSError covers connection refused when the container is down.
        logger.exception("Database health check failed")
        return False
