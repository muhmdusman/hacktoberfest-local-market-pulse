"""Aggregates all feature routers under a single API router."""

from fastapi import APIRouter

from app.api.routes import dashboard, health, scans

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(scans.router)  # internal/debug API; frontend uses /runs
