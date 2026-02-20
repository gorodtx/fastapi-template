from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import uuid4

import sqlalchemy as sa

from backend.application.common.interfaces.ports.cache import StrCache
from backend.application.common.interfaces.ports.persistence.manager import (
    SessionProtocol,
    TransactionManager,
)
from backend.application.common.interfaces.ports.system_health import (
    SystemHealthPort,
)
from backend.infrastructure.persistence.sqlalchemy.session_db import (
    require_async_session,
)

_LOGGER = logging.getLogger(__name__)
_HEALTH_CACHE_KEY_PREFIX = "system:health"


async def _ping_database(session: SessionProtocol) -> int:
    async_session = require_async_session(session)
    result = await async_session.execute(sa.text("SELECT 1"))
    value = result.scalar_one()
    if isinstance(value, int):
        return value
    raise TypeError("Database ping returned non-integer payload")


@dataclass(frozen=True, slots=True)
class InfrastructureSystemHealthProbe(SystemHealthPort):
    manager: TransactionManager
    cache: StrCache

    async def is_db_alive(
        self: InfrastructureSystemHealthProbe,
    ) -> bool:
        try:
            return await self.manager.send(_ping_database) == 1
        except Exception:
            _LOGGER.exception("Database health check failed")
            return False

    async def is_redis_alive(
        self: InfrastructureSystemHealthProbe,
    ) -> bool:
        key = f"{_HEALTH_CACHE_KEY_PREFIX}:{uuid4()}"
        try:
            await self.cache.increment(key, delta=1)
            await self.cache.delete(key)
            return True
        except Exception:
            _LOGGER.exception("Redis health check failed")
            return False
