from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.http.api.schemas.system import (
    SystemMetricsResponse,
    SystemStatusResponse,
)

router: APIRouter = APIRouter(route_class=DishkaRoute)


@router.get("/system", response_model=SystemStatusResponse)
async def system_status() -> SystemStatusResponse:
    return SystemStatusResponse(status="ok")


@router.get("/system/metrics", response_model=SystemMetricsResponse)
async def system_metrics() -> SystemMetricsResponse:
    return SystemMetricsResponse(status="ok", metrics={})
