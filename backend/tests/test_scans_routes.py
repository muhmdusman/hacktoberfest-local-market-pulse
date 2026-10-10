"""Tests for app/api/routes/scans.py, app/services/scan_service.py and app/schemas/scan.py."""

import uuid

import pytest
from sqlalchemy import delete

from app.agents.graph import build_scan_graph
from app.api.routes import scans as scans_routes
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.llm.factory import LLMNotConfiguredError
from app.models.scan import Scan
from app.services import scan_service
from tests.fakes import AuthenticationError, FakeLLM

PREFIX = f"{get_settings().api_v1_prefix}/scans"
BODY = {"business": "cafe", "city": "Islamabad", "sources": ["web", "reddit"], "max_results": 4}


@pytest.fixture
def created_ids():
    ids: list[str] = []
    yield ids


@pytest.fixture(autouse=True)
async def _cleanup(created_ids):
    yield
    if created_ids:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Scan).where(Scan.id.in_([uuid.UUID(i) for i in created_ids])))
            await db.commit()


def use_llm(monkeypatch, llm):
    monkeypatch.setattr(scan_service, "build_graph", lambda: build_scan_graph(llm))


async def test_scan_runs_in_background_and_results_are_stored(client, fake_search, monkeypatch, created_ids):
    use_llm(monkeypatch, FakeLLM())
    created = await client.post(PREFIX, json=BODY)
    assert created.status_code == 202
    scan_id = created.json()["scan_id"]
    created_ids.append(scan_id)

    status = (await client.get(f"{PREFIX}/{scan_id}")).json()
    assert (status["status"], status["stage"]) == ("done", "done")
    assert len(status["queries"]) == 2

    body = (await client.get(f"{PREFIX}/{scan_id}/results")).json()
    assert len(body["results"]) == 4
    first = body["results"][0]
    assert first["status"] == "ok" and first["sentiment"] == "neg" and first["model"] == "fake-7b"
    assert body["summary"]["totals"]["relevant"] == 4
    assert body["summary"]["actions_source"] == "model"

    listed = (await client.get(PREFIX)).json()
    assert scan_id in [s["id"] for s in listed]


async def test_relevant_only_filter(client, fake_search, monkeypatch, created_ids):
    use_llm(monkeypatch, FakeLLM(insight={"relevant": False, "sentiment": "neutral", "confidence": 0.5}))
    scan_id = (await client.post(PREFIX, json=BODY)).json()["scan_id"]
    created_ids.append(scan_id)
    body = (await client.get(f"{PREFIX}/{scan_id}/results", params={"relevant_only": True})).json()
    assert body["results"] == []


async def test_fatal_llm_error_marks_scan_failed(client, fake_search, monkeypatch, created_ids):
    use_llm(monkeypatch, FakeLLM(error=AuthenticationError("invalid api key")))
    scan_id = (await client.post(PREFIX, json=BODY)).json()["scan_id"]
    created_ids.append(scan_id)
    status = (await client.get(f"{PREFIX}/{scan_id}")).json()
    assert status["status"] == "failed"
    assert status["error"].startswith("AuthenticationError")


async def test_results_409_while_running(client, db_session, created_ids):
    scan = Scan(business="cafe", city="Islamabad", sources=["web"], max_results=5, model="m", status="running", stage="evaluating")
    db_session.add(scan)
    await db_session.commit()
    created_ids.append(str(scan.id))
    response = await client.get(f"{PREFIX}/{scan.id}/results")
    assert response.status_code == 409


async def test_unknown_scan_404(client):
    missing = uuid.uuid4()
    assert (await client.get(f"{PREFIX}/{missing}")).status_code == 404
    assert (await client.get(f"{PREFIX}/{missing}/results")).status_code == 404


@pytest.mark.parametrize(
    "body",
    [{}, {"business": "cafe", "sources": []}, {"business": "cafe", "sources": ["tiktok"]}, {"business": "cafe", "max_results": 500}],
)
async def test_invalid_body_422(client, body):
    assert (await client.post(PREFIX, json=body)).status_code == 422


async def test_503_when_llm_not_configured(client, monkeypatch):
    def not_ready():
        raise LLMNotConfiguredError("GROQ_API_KEY is missing from .env.local")

    monkeypatch.setattr(scans_routes, "ensure_llm_ready", not_ready)
    response = await client.post(PREFIX, json=BODY)
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]
