"""Frontend contract endpoints used by the Next.js Local Market Pulse dashboard."""

import shutil
import subprocess
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Response, status

from app.api.deps import DbSession
from app.llm.factory import LLMNotConfiguredError, ensure_llm_ready
from app.llm.registry import MAX_PARAMS_B, REGISTRY, ModelNotAllowedError, resolve_model
from app.schemas.run import RunCreate, RunCreated, RunResultsOut, RunStatusOut
from app.schemas.scan import ScanCreate
from app.services import dashboard_service, scan_service

router = APIRouter()

BUSINESS_TYPES = ["cafe", "restaurant", "gym", "salon", "other"]
AREAS = ["F-6", "F-7", "F-8", "F-10", "F-11", "G-9", "G-11", "E-7", "Blue Area", "DHA", "Bahria"]
DEFAULT_COMPETITORS = ["Brew Bastion", "Chai Chowk", "Kahwa House", "Daily Grind ISB"]


async def _scan_or_404(db: DbSession, run_id: UUID):
    scan = await scan_service.get_scan(db, run_id)
    if scan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Run {run_id} not found")
    return scan


def _probe(command: str) -> tuple[str, str]:
    path = shutil.which(command)
    if not path:
        return "missing", f"{command} is not installed"
    try:
        result = subprocess.run([path, "--version"], capture_output=True, timeout=4, check=False)
        return ("ok", "") if result.returncode == 0 else ("broken", f"{command} exists but its health probe failed")
    except subprocess.TimeoutExpired:
        return "timeout", f"{command} health probe timed out"
    except OSError:
        return "broken", f"{command} exists but cannot execute"


@router.get("/options")
async def options():
    """Static form options and validation limits for the dashboard."""
    return {"business_types": BUSINESS_TYPES, "default_city": "Islamabad", "areas": AREAS, "default_competitors": DEFAULT_COMPETITORS, "sources": ["reddit", "web"], "modes": ["cached", "live"], "limits": {"max_urls": 10, "max_limit": 200}}


@router.get("/models")
async def models():
    """Active model, strategies and the full registry showing the enforced ≤8B rule."""
    active = ensure_llm_ready()
    return {
        "max_params_rule": "≤ 8B class (exact ≤ 8.5B), open-weight only",
        "provider": active.provider,
        "tiers": {"small": {"id": active.id, "strategy": "compact JSON planning"}, "large": {"id": active.id, "strategy": "validated extraction + repair"}},
        "models": [{"id": m.id, "provider": m.provider, "nominal_size": f"{m.params_b:g}B", "params_b": m.params_b, "license": m.license, "tier": "small|large" if m.id == active.id else "available", "open_weight": m.open_weight, "eligible": m.eligible} for m in REGISTRY.values()],
    }


@router.get("/sources/status")
async def sources_status():
    """Ordered collector capability status, inspired by Agent-Reach's probe pattern."""
    rdt_status, rdt_hint = _probe("rdt")
    return {"sources": [
        {"source": "reddit", "active": "ddgs-site-search", "backends": [{"name": "rdt", "status": rdt_status, "hint": rdt_hint}, {"name": "ddgs-site-search", "status": "ok", "hint": "Public discovery; no Reddit login or posting"}]},
        {"source": "web", "active": "ddgs", "backends": [{"name": "ddgs", "status": "ok", "hint": "Public metasearch"}]},
    ]}


@router.post("/runs", status_code=status.HTTP_202_ACCEPTED, response_model=RunCreated)
async def create_run(body: RunCreate, db: DbSession, background: BackgroundTasks):
    """Queue the planner → tools → evaluator → strategist workflow."""
    try:
        ensure_llm_ready()
    except (LLMNotConfiguredError, ModelNotAllowedError) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    scan = await scan_service.create_scan(db, ScanCreate(business=body.business, city=body.city, areas=body.areas, competitors=body.competitors, sources=body.sources, max_results=body.limit))
    background.add_task(scan_service.run_scan, scan.id)
    return RunCreated(run_id=scan.id, status=scan.status)


@router.get("/runs/{run_id}", response_model=RunStatusOut)
async def get_run(run_id: UUID, db: DbSession):
    """Poll the current workflow stage and counters."""
    scan = await _scan_or_404(db, run_id)
    results = await scan_service.get_results(db, run_id)
    return dashboard_service.status_payload(scan, results)


@router.get("/runs/{run_id}/results", response_model=RunResultsOut)
async def get_run_results(run_id: UUID, db: DbSession):
    """Return the complete dashboard report, evidence and harness metrics."""
    scan = await _scan_or_404(db, run_id)
    if scan.status in ("queued", "running"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Run is still {scan.stage}")
    if scan.status == "failed":
        raise HTTPException(status.HTTP_409_CONFLICT, scan.error or "Run failed")
    results = await scan_service.get_results(db, run_id)
    return dashboard_service.build_results(scan, results)


@router.get("/runs/{run_id}/report.{format}")
async def download_report(run_id: UUID, format: Literal["md", "html"], db: DbSession):
    """Download the completed report as Markdown or standalone HTML."""
    scan = await _scan_or_404(db, run_id)
    if scan.status != "done":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Run is {scan.status}")
    payload = dashboard_service.build_results(scan, await scan_service.get_results(db, run_id))
    content = dashboard_service.render_markdown(scan, payload) if format == "md" else dashboard_service.render_html(scan, payload)
    media = "text/markdown; charset=utf-8" if format == "md" else "text/html; charset=utf-8"
    return Response(content, media_type=media, headers={"Content-Disposition": f'attachment; filename="local-market-pulse-{run_id}.{format}"'})
