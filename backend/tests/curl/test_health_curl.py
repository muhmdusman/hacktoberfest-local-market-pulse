"""Live curl checks for the health endpoints.

Needs a running server:
    uv run uvicorn app.main:app --port 8000
Then:
    uv run pytest -m live

Skipped automatically when curl is missing or the server isn't reachable.
Override the target with API_BASE_URL (default http://localhost:8000).
"""

import json
import os
import shutil
import subprocess

import pytest

from app.core.config import get_settings

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
PREFIX = get_settings().api_v1_prefix
CURL = shutil.which("curl")

pytestmark = pytest.mark.live


def curl_get(path: str) -> tuple[int, dict]:
    """GET BASE_URL+path with curl; return (status_code, parsed_json_body)."""
    # Argument list (no shell) so the URL is never interpreted by a shell.
    result = subprocess.run(
        [CURL, "-s", "-m", "5", "-w", "\n%{http_code}", f"{BASE_URL}{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"Server not reachable at {BASE_URL} (curl exit {result.returncode})")
    body, _, status = result.stdout.rpartition("\n")
    return int(status), json.loads(body)


@pytest.fixture(autouse=True)
def _require_curl():
    if CURL is None:
        pytest.skip("curl is not installed")


def test_curl_health():
    status, body = curl_get(f"{PREFIX}/health")
    assert status == 200
    assert body == {"status": "ok"}


def test_curl_health_db():
    status, body = curl_get(f"{PREFIX}/health/db")
    assert status == 200
    assert body == {"status": "ok", "database": "up"}
