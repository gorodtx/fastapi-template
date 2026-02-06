from __future__ import annotations

from backend.presentation.http.api.schemas.base import BaseShema


class SystemStatusResponse(BaseShema):
    status: str


class SystemMetricsResponse(BaseShema):
    status: str
    metrics: dict[str, float]
