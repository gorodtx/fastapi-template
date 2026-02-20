from __future__ import annotations

from backend.application.common.dtos.base import dto


@dto
class GetSystemStatusDTO: ...


@dto
class SystemChecksDTO:
    db: str
    redis: str


@dto
class SystemStatusDTO:
    status: str
    checks: SystemChecksDTO
