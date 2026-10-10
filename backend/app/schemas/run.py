"""Frontend-facing request and response contracts for /runs."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class RunCreate(BaseModel):
    business: str = Field(min_length=1, max_length=60)
    city: str = Field(default="Islamabad", min_length=1, max_length=60)
    areas: list[str] = Field(default_factory=list, max_length=12)
    competitors: list[str] = Field(default_factory=list, max_length=10)
    sources: list[Literal["reddit", "web"]] = Field(default_factory=lambda: ["reddit", "web"], min_length=1)
    mode: Literal["cached", "live"] = "live"
    urls: list[HttpUrl] = Field(default_factory=list, max_length=10)
    limit: int = Field(default=20, ge=1, le=200)
    provider: str | None = None
    votes: int = Field(default=1, ge=1, le=5)

    @field_validator("business", "city")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class RunCreated(BaseModel):
    run_id: UUID
    status: Literal["queued", "running", "done", "failed"]


class RunProgress(BaseModel):
    done: int
    total: int


class RunCounts(BaseModel):
    collected: int
    deduped: int
    kept: int
    filtered: int
    escalated: int
    failed: int


class RunMessage(BaseModel):
    level: Literal["info", "warn", "error"]
    text: str


class RunStatusOut(BaseModel):
    run_id: UUID
    status: Literal["queued", "running", "done", "failed"]
    stage: Literal["collecting", "analyzing", "trending", "reporting", "done"]
    progress: RunProgress
    counts: RunCounts
    messages: list[RunMessage]
    created_at: datetime
    finished_at: datetime | None
    error: dict[str, str] | None


class RunResultsOut(BaseModel):
    run_id: UUID
    provenance: dict[str, Any]
    overview: dict[str, Any]
    keywords: list[dict[str, Any]]
    voice: dict[str, Any]
    competitors: list[dict[str, Any]]
    gaps: list[dict[str, Any]]
    content: dict[str, Any]
    threads: list[dict[str, Any]]
    participation_note: str
    metrics: dict[str, Any]
