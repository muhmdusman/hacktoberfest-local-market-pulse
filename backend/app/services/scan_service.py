"""Scan lifecycle: create -> run the agent graph in the background -> persist results."""

import logging
import time
import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import build_scan_graph
from app.agents.state import initial_state
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.llm.factory import get_chat_model
from app.models.scan import Scan, ScanResult, utcnow
from app.schemas.scan import ScanCreate

log = logging.getLogger("scan")

# Stage shown to clients after each node finishes.
NEXT_STAGE = {
    "planner": "searching",
    "search": "collecting",
    "collector": "evaluating",
    "evaluator": "summarizing",
    "strategist": "saving",
}


def build_graph():
    """Default graph: registry-approved Groq model + real search tools. Tests patch this."""
    return build_scan_graph(get_chat_model())


def _tag(scan_id: Any) -> str:
    return str(scan_id)[:8]


async def create_scan(db: AsyncSession, body: ScanCreate) -> Scan:
    scan = Scan(
        business=body.business,
        city=body.city,
        areas=body.areas,
        competitors=body.competitors,
        sources=body.sources,
        max_results=body.max_results,
        model=get_settings().llm_model,
    )
    db.add(scan)
    await db.commit()
    log.info("queued %s · %s in %s · %s", _tag(scan.id), scan.business, scan.city, "+".join(scan.sources))
    return scan


def _to_row(scan_id: uuid.UUID, position: int, item: dict[str, Any]) -> ScanResult:
    insight = item.get("insight") or {}
    return ScanResult(
        scan_id=scan_id,
        position=position,
        source=item["source"],
        query=item["query"][:200],
        url=item["url"],
        title=item["title"][:300],
        snippet=item["snippet"],
        status=item["status"],
        relevant=insight.get("relevant"),
        sentiment=insight.get("sentiment"),
        confidence=insight.get("confidence"),
        insight=item.get("insight"),
        model=item.get("model"),
        attempts=item.get("attempts", 0),
        repairs=item.get("repairs", 0),
        latency_ms=item.get("latency_ms", 0),
        error=item.get("error"),
    )


async def run_scan(scan_id: uuid.UUID) -> None:
    """Background job. Streams graph updates to record the stage, then saves everything."""
    started = time.perf_counter()
    async with AsyncSessionLocal() as db:
        scan = await db.get(Scan, scan_id)
        if scan is None:
            log.error("scan %s not found", _tag(scan_id))
            return
        scan.status, scan.stage = "running", "planning"
        await db.commit()

        try:
            graph = build_graph()
            final: dict[str, Any] = {}
            async for mode, chunk in graph.astream(initial_state(scan), stream_mode=["updates", "values"]):
                if mode == "values":
                    final = chunk
                    continue
                for node, delta in chunk.items():
                    if node == "planner" and delta:
                        scan.queries = delta.get("queries", [])
                    scan.stage = NEXT_STAGE.get(node, scan.stage)
                await db.commit()

            evaluated = final.get("evaluated", [])
            db.add_all(_to_row(scan.id, i, item) for i, item in enumerate(evaluated))
            scan.summary = final.get("summary") or {}
            scan.status, scan.stage, scan.finished_at = "done", "done", utcnow()
            await db.commit()
            log.info(
                "done %s · %d results · %d relevant · %.1fs",
                _tag(scan_id),
                len(evaluated),
                scan.summary.get("totals", {}).get("relevant", 0),
                time.perf_counter() - started,
            )
        except Exception as exc:
            message = f"{type(exc).__name__}: {' '.join(str(exc).split())}"[:500]
            log.error("failed %s · %s", _tag(scan_id), message, exc_info=log.isEnabledFor(logging.DEBUG))
            await db.rollback()
            await db.execute(
                update(Scan)
                .where(Scan.id == scan_id)
                .values(status="failed", stage="failed", error=message, finished_at=utcnow())
            )
            await db.commit()


async def list_scans(db: AsyncSession, limit: int = 20) -> list[Scan]:
    rows = await db.scalars(select(Scan).order_by(Scan.created_at.desc()).limit(limit))
    return list(rows)


async def get_scan(db: AsyncSession, scan_id: uuid.UUID) -> Scan | None:
    return await db.get(Scan, scan_id)


async def get_results(db: AsyncSession, scan_id: uuid.UUID, relevant_only: bool = False) -> list[ScanResult]:
    stmt = select(ScanResult).where(ScanResult.scan_id == scan_id).order_by(ScanResult.position)
    if relevant_only:
        stmt = stmt.where(ScanResult.relevant.is_(True))
    return list(await db.scalars(stmt))
