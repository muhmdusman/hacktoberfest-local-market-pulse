"""ORM models: a Scan (one market study) has many ScanResults (evaluated search hits)."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business: Mapped[str] = mapped_column(String(60))
    city: Mapped[str] = mapped_column(String(60))
    areas: Mapped[list[str]] = mapped_column(JSONB, default=list)
    competitors: Mapped[list[str]] = mapped_column(JSONB, default=list)
    sources: Mapped[list[str]] = mapped_column(JSONB, default=list)
    max_results: Mapped[int] = mapped_column(Integer, default=20)

    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)  # queued|running|done|failed
    stage: Mapped[str] = mapped_column(String(16), default="queued")
    model: Mapped[str] = mapped_column(String(80))
    queries: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    results: Mapped[list["ScanResult"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True, order_by="ScanResult.position"
    )


class ScanResult(Base):
    __tablename__ = "scan_results"
    __table_args__ = (UniqueConstraint("scan_id", "url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)

    # What the search tool found
    source: Mapped[str] = mapped_column(String(16))  # web | reddit
    query: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(2048))
    title: Mapped[str] = mapped_column(String(300))
    snippet: Mapped[str] = mapped_column(Text)

    # What the evaluator extracted (promoted columns are filterable; full JSON in `insight`)
    status: Mapped[str] = mapped_column(String(16))  # ok | failed
    relevant: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(16), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    insight: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Harness trace
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    repairs: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    scan: Mapped[Scan] = relationship(back_populates="results")
