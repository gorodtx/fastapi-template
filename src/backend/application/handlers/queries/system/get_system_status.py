from __future__ import annotations

from backend.application.common.dtos.system import (
    GetSystemStatusDTO,
    SystemChecksDTO,
    SystemStatusDTO,
)
from backend.application.common.exceptions.application import AppError
from backend.application.common.interfaces.ports.system_health import (
    SystemHealthPort,
)
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.result import Result, ResultImpl
from backend.application.handlers.transform import handler


class GetSystemStatusQuery(GetSystemStatusDTO): ...


@handler(mode="read")
class GetSystemStatusHandler(
    QueryHandler[GetSystemStatusQuery, SystemStatusDTO]
):
    probe: SystemHealthPort

    async def __call__(
        self: GetSystemStatusHandler,
        query: GetSystemStatusQuery,
        /,
    ) -> Result[SystemStatusDTO, AppError]:
        _ = query
        db_ok = await self.probe.is_db_alive()
        redis_ok = await self.probe.is_redis_alive()
        return ResultImpl.ok(
            SystemStatusDTO(
                status="ok" if db_ok and redis_ok else "degraded",
                checks=SystemChecksDTO(
                    db="ok" if db_ok else "fail",
                    redis="ok" if redis_ok else "fail",
                ),
            )
        )
