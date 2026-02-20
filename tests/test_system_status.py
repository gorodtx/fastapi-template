from __future__ import annotations

from dataclasses import dataclass

import pytest
from starlette.responses import Response

from backend.application.common.interfaces.ports.system_health import (
    SystemHealthPort,
)
from backend.presentation.http.api.routing import system as system_route


@dataclass(slots=True)
class _ProbeStub(SystemHealthPort):
    db_ok: bool
    redis_ok: bool

    async def is_db_alive(self: _ProbeStub) -> bool:
        return self.db_ok

    async def is_redis_alive(self: _ProbeStub) -> bool:
        return self.redis_ok


@pytest.mark.asyncio
async def test_system_status_returns_ok() -> None:
    response = Response()
    payload = await system_route.system_status(
        response=response,
        probe=_ProbeStub(db_ok=True, redis_ok=True),
    )

    assert response.status_code == 200
    assert payload.status == "ok"
    assert payload.checks.db == "ok"
    assert payload.checks.redis == "ok"


@pytest.mark.asyncio
async def test_system_status_returns_degraded_when_dependency_fails() -> None:
    response = Response()
    payload = await system_route.system_status(
        response=response,
        probe=_ProbeStub(db_ok=False, redis_ok=True),
    )

    assert response.status_code == 503
    assert payload.status == "degraded"
    assert payload.checks.db == "fail"
    assert payload.checks.redis == "ok"
