from __future__ import annotations

from typing import Literal

from backend.presentation.http.api.schemas.base import BaseSchema


class SystemChecksResponse(BaseSchema):
    db: Literal["ok", "fail"]
    redis: Literal["ok", "fail"]


class SystemStatusResponse(BaseSchema):
    status: Literal["ok", "degraded"]
    checks: SystemChecksResponse
