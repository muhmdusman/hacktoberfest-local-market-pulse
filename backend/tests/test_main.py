"""Tests for app/main.py"""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app, create_app

PREFIX = get_settings().api_v1_prefix


def test_create_app_uses_configured_title():
    assert create_app().title == get_settings().app_name


def test_routes_are_mounted_under_api_prefix():
    # OpenAPI paths are the public view of mounted routes (app.routes holds
    # lazily-included router objects in recent FastAPI versions).
    paths = app.openapi()["paths"]
    assert f"{PREFIX}/health" in paths
    assert f"{PREFIX}/health/db" in paths


def test_lifespan_starts_against_postgres_and_serves_requests():
    # Entering the context runs the lifespan startup (init_db against Postgres).
    with TestClient(app) as test_client:
        response = test_client.get(f"{PREFIX}/health/db")
    assert response.status_code == 200
    assert response.json()["database"] == "up"
