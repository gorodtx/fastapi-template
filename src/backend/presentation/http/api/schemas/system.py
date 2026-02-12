from __future__ import annotations

from backend.presentation.http.api.schemas.base import BaseSchema


class SystemStatusResponse(BaseSchema):
    status: str
