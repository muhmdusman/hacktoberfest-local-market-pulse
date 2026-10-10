"""Tests for app/api/routes/health.py"""

from app.api.deps import get_db
from app.core.config import get_settings
from app.main import app
from tests.conftest import BrokenSession

PREFIX = get_settings().api_v1_prefix


async def test_health_returns_ok(client):
    response = await client.get(f"{PREFIX}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_db_returns_up_when_postgres_reachable(client):
    response = await client.get(f"{PREFIX}/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


async def test_health_db_returns_503_when_postgres_unreachable(client):
    async def broken_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    try:
        response = await client.get(f"{PREFIX}/health/db")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "down"}
