from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from starlette.responses import Response

from backend.presentation.http.api.routing import system as system_route


@dataclass(slots=True)
class _CacheStub:
    fail_increment: bool = False
    fail_delete: bool = False
    increment_calls: list[str] = field(default_factory=list)
    delete_calls: list[str] = field(default_factory=list)

    async def increment(self: _CacheStub, key: str, *, delta: int = 1) -> int:
        _ = delta
        self.increment_calls.append(key)
        if self.fail_increment:
            raise RuntimeError("increment failed")
        return 1

    async def delete(self: _CacheStub, key: str) -> None:
        self.delete_calls.append(key)
        if self.fail_delete:
            raise RuntimeError("delete failed")


@pytest.mark.asyncio
async def test_system_status_returns_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _db_ok(_manager: object) -> bool:
        return True

    async def _redis_ok(_cache: object) -> bool:
        return True

    monkeypatch.setattr(system_route, "_is_db_alive", _db_ok)
    monkeypatch.setattr(system_route, "_is_redis_alive", _redis_ok)

    response = Response()
    payload = await system_route.system_status(
        response=response,
        manager=object(),
        cache=object(),
    )

    assert response.status_code == 200
    assert payload.status == "ok"
    assert payload.checks.db == "ok"
    assert payload.checks.redis == "ok"


@pytest.mark.asyncio
async def test_system_status_returns_degraded_when_dependency_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _db_fail(_manager: object) -> bool:
        return False

    async def _redis_ok(_cache: object) -> bool:
        return True

    monkeypatch.setattr(system_route, "_is_db_alive", _db_fail)
    monkeypatch.setattr(system_route, "_is_redis_alive", _redis_ok)

    response = Response()
    payload = await system_route.system_status(
        response=response,
        manager=object(),
        cache=object(),
    )

    assert response.status_code == 503
    assert payload.status == "degraded"
    assert payload.checks.db == "fail"
    assert payload.checks.redis == "ok"


@pytest.mark.asyncio
async def test_is_redis_alive_returns_true_on_success() -> None:
    cache = _CacheStub()

    ok = await system_route._is_redis_alive(cache)

    assert ok is True
    assert len(cache.increment_calls) == 1
    assert cache.increment_calls == cache.delete_calls


@pytest.mark.asyncio
async def test_is_redis_alive_returns_false_on_error() -> None:
    cache = _CacheStub(fail_increment=True)

    ok = await system_route._is_redis_alive(cache)

    assert ok is False
