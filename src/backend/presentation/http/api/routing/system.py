from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Response, status

from backend.application.common.interfaces.ports.system_health import (
    SystemHealthPort,
)
from backend.application.handlers.queries.system.get_system_status import (
    GetSystemStatusHandler,
    GetSystemStatusQuery,
)
from backend.presentation.http.api.routing.helpers import (
    unwrap_result,
)
from backend.presentation.http.api.schemas.system import (
    SystemStatusResponse,
)

router: APIRouter = APIRouter(route_class=DishkaRoute)


@router.get("/system", response_model=SystemStatusResponse)
async def system_status(
    response: Response,
    probe: FromDishka[SystemHealthPort],
) -> SystemStatusResponse:
    handler = GetSystemStatusHandler(probe=probe)
    dto = await unwrap_result(handler(GetSystemStatusQuery()))
    payload = SystemStatusResponse.from_dto(dto)
    if payload.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload
