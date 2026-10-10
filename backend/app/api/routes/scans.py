"""Scan endpoints: start a market scan, poll it, read the evaluated results."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.api.deps import DbSession
from app.llm.factory import LLMNotConfiguredError, ensure_llm_ready
from app.llm.registry import ModelNotAllowedError
from app.schemas.scan import ScanCreate, ScanCreated, ScanOut, ScanResultsOut
from app.services import scan_service

router = APIRouter(prefix="/scans", tags=["scans"])


async def _get_or_404(db: DbSession, scan_id: UUID):
    scan = await scan_service.get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Scan {scan_id} not found")
    return scan


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=ScanCreated)
async def start_scan(body: ScanCreate, db: DbSession, background: BackgroundTasks) -> ScanCreated:
    """Queue a scan. The planner -> search -> evaluator -> strategist graph runs in the background."""
    try:
        ensure_llm_ready()
    except (LLMNotConfiguredError, ModelNotAllowedError) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    scan = await scan_service.create_scan(db, body)
    background.add_task(scan_service.run_scan, scan.id)
    return ScanCreated(scan_id=scan.id, status=scan.status)


@router.get("", response_model=list[ScanOut])
async def list_scans(db: DbSession, limit: int = Query(20, ge=1, le=100)):
    """Most recent scans first."""
    return await scan_service.list_scans(db, limit)


@router.get("/{scan_id}", response_model=ScanOut)
async def get_scan(scan_id: UUID, db: DbSession):
    """Status and current stage. Poll this until status is done or failed."""
    return await _get_or_404(db, scan_id)


@router.get("/{scan_id}/results", response_model=ScanResultsOut)
async def get_scan_results(scan_id: UUID, db: DbSession, relevant_only: bool = False) -> ScanResultsOut:
    """Summary (pain points, requests, keywords, competitors, actions) plus every evaluated result."""
    scan = await _get_or_404(db, scan_id)
    if scan.status in ("queued", "running"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Scan is still {scan.stage}")
    results = await scan_service.get_results(db, scan_id, relevant_only)
    return ScanResultsOut(
        scan=ScanOut.model_validate(scan),
        summary=scan.summary,
        results=results,
    )
