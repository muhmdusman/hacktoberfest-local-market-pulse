"""Health endpoints: process liveness and database connectivity."""

from fastapi import APIRouter, Response, status

from app.api.deps import DbSession
from app.schemas.health import DatabaseHealthResponse, HealthResponse
from app.services.health_service import check_database

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe. Does not touch the database."""
    return HealthResponse(status="ok")


@router.get(
    "/db",
    response_model=DatabaseHealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": DatabaseHealthResponse}},
)
async def health_db(db: DbSession, response: Response) -> DatabaseHealthResponse:
    """Readiness probe. Returns 503 when Postgres is unreachable."""
    if await check_database(db):
        return DatabaseHealthResponse(status="ok", database="up")

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return DatabaseHealthResponse(status="error", database="down")
