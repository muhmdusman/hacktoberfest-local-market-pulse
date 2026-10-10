"""Live curl check for the scan flow (real web search + real Groq model).

Needs a running server:  uv run uvicorn app.main:app --port 8000
Run:                     uv run pytest -m live tests/curl/test_scans_curl.py
"""

import json
import os
import shutil
import subprocess
import time

import pytest

from app.core.config import get_settings

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
PREFIX = f"{BASE_URL}{get_settings().api_v1_prefix}/scans"
CURL = shutil.which("curl")

pytestmark = pytest.mark.live


def curl(*args: str) -> tuple[int, dict]:
    result = subprocess.run(
        [CURL, "-s", "-m", "30", "-w", "\n%{http_code}", *args], capture_output=True, text=True, encoding="utf-8", check=False
    )
    if result.returncode != 0:
        pytest.skip(f"Server not reachable at {BASE_URL} (curl exit {result.returncode})")
    body, _, code = result.stdout.rpartition("\n")
    return int(code), json.loads(body)


@pytest.fixture(autouse=True)
def _require_curl():
    if CURL is None:
        pytest.skip("curl is not installed")


def test_curl_scan_end_to_end():
    payload = json.dumps({"business": "cafe", "city": "Islamabad", "sources": ["web", "reddit"], "max_results": 6})
    code, created = curl("-X", "POST", PREFIX, "-H", "Content-Type: application/json", "-d", payload)
    assert code == 202, created
    scan_id = created["scan_id"]

    deadline = time.monotonic() + 180
    status = {}
    while time.monotonic() < deadline:
        _, status = curl(f"{PREFIX}/{scan_id}")
        if status["status"] in ("done", "failed"):
            break
        time.sleep(2)
    assert status["status"] == "done", status.get("error")

    code, body = curl(f"{PREFIX}/{scan_id}/results")
    assert code == 200
    assert body["results"], "expected at least one evaluated result"
    assert all(r["status"] in ("ok", "failed") for r in body["results"])
    assert body["summary"]["actions"]
