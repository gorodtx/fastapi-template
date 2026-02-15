from __future__ import annotations

import logging
from uuid import uuid4

import sqlalchemy as sa
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Response, status

from backend.application.common.interfaces.ports.cache import StrCache
from backend.application.common.interfaces.ports.persistence.manager import (
    SessionProtocol,
    TransactionManager,
)
from backend.infrastructure.persistence.sqlalchemy.session_db import (
    require_async_session,
)
from backend.presentation.http.api.schemas.system import (
    SystemChecksResponse,
    SystemStatusResponse,
)

router: APIRouter = APIRouter(route_class=DishkaRoute)
_LOGGER = logging.getLogger(__name__)
_HEALTH_CACHE_KEY_PREFIX = "system:health"


async def _ping_database(session: SessionProtocol) -> int:
    async_session = require_async_session(session)
    result = await async_session.execute(sa.text("SELECT 1"))
    value = result.scalar_one()
    if isinstance(value, int):
        return value
    raise TypeError("Database ping returned non-integer payload")


async def _is_db_alive(manager: TransactionManager) -> bool:
    try:
        return await manager.send(_ping_database) == 1
    except Exception:
        _LOGGER.exception("Database health check failed")
        return False


async def _is_redis_alive(cache: StrCache) -> bool:
    key = f"{_HEALTH_CACHE_KEY_PREFIX}:{uuid4()}"
    try:
        await cache.increment(key, delta=1)
        await cache.delete(key)
        return True
    except Exception:
        _LOGGER.exception("Redis health check failed")
        return False


@router.get("/system", response_model=SystemStatusResponse)
async def system_status(
    response: Response,
    manager: FromDishka[TransactionManager],
    cache: FromDishka[StrCache],
) -> SystemStatusResponse:
    db_ok = await _is_db_alive(manager)
    redis_ok = await _is_redis_alive(cache)
    payload = SystemStatusResponse(
        status="ok" if db_ok and redis_ok else "degraded",
        checks=SystemChecksResponse(
            db="ok" if db_ok else "fail",
            redis="ok" if redis_ok else "fail",
        ),
    )
    if payload.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload
