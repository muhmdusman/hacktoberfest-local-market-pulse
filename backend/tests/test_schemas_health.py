"""Tests for app/schemas/health.py"""

import pytest
from pydantic import ValidationError

from app.schemas.health import DatabaseHealthResponse, HealthResponse


def test_health_response_accepts_ok():
    assert HealthResponse(status="ok").model_dump() == {"status": "ok"}


def test_health_response_rejects_unknown_status():
    with pytest.raises(ValidationError):
        HealthResponse(status="degraded")


@pytest.mark.parametrize(
    ("status", "database"),
    [("ok", "up"), ("error", "down")],
)
def test_database_health_response_accepts_valid_pairs(status, database):
    body = DatabaseHealthResponse(status=status, database=database)
    assert body.model_dump() == {"status": status, "database": database}


def test_database_health_response_rejects_unknown_database_state():
    with pytest.raises(ValidationError):
        DatabaseHealthResponse(status="ok", database="maybe")
