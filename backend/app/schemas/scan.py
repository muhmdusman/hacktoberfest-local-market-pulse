"""Request/response models for the scans API."""

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Source = Literal["web", "reddit"]


class ScanCreate(BaseModel):
    business: ShortText = Field(examples=["cafe"])
    city: ShortText = "Islamabad"
    areas: list[ShortText] = Field(default_factory=list, max_length=12, examples=[["F-7", "G-11"]])
    competitors: list[ShortText] = Field(default_factory=list, max_length=10)
    sources: list[Source] = Field(default_factory=lambda: ["web", "reddit"], min_length=1)
    max_results: int = Field(20, ge=1, le=200)

    @field_validator("sources")
    @classmethod
    def _dedupe(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(v))


class ScanCreated(BaseModel):
    scan_id: UUID
    status: str


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business: str
    city: str
    areas: list[str]
    competitors: list[str]
    sources: list[str]
    max_results: int
    status: str
    stage: str
    model: str
    queries: list[dict[str, Any]]
    error: str | None
    created_at: datetime
    finished_at: datetime | None


class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: int
    source: str
    query: str
    url: str
    title: str
    snippet: str
    status: str
    relevant: bool | None
    sentiment: str | None
    confidence: float | None
    insight: dict[str, Any] | None
    model: str | None
    attempts: int
    repairs: int
    latency_ms: int
    error: str | None


class ScanResultsOut(BaseModel):
    scan: ScanOut
    summary: dict[str, Any] | None
    results: list[ResultOut]
