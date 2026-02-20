from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from backend.infrastructure.system_health import (
    InfrastructureSystemHealthProbe,
)


@dataclass(slots=True)
class _ManagerStub:
    result: int = 1
    fail: bool = False

    async def send(self: _ManagerStub, _query: object) -> int:
        if self.fail:
            raise RuntimeError("db failed")
        return self.result


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
async def test_system_health_probe_db_alive_on_select_1() -> None:
    probe = InfrastructureSystemHealthProbe(
        manager=_ManagerStub(result=1), cache=_CacheStub()
    )

    assert await probe.is_db_alive() is True


@pytest.mark.asyncio
async def test_system_health_probe_db_alive_false_on_exception() -> None:
    probe = InfrastructureSystemHealthProbe(
        manager=_ManagerStub(fail=True), cache=_CacheStub()
    )

    assert await probe.is_db_alive() is False


@pytest.mark.asyncio
async def test_system_health_probe_redis_alive_true_on_success() -> None:
    cache = _CacheStub()
    probe = InfrastructureSystemHealthProbe(
        manager=_ManagerStub(), cache=cache
    )

    assert await probe.is_redis_alive() is True
    assert len(cache.increment_calls) == 1
    assert cache.increment_calls == cache.delete_calls


@pytest.mark.asyncio
async def test_system_health_probe_redis_alive_false_on_increment_error() -> (
    None
):
    probe = InfrastructureSystemHealthProbe(
        manager=_ManagerStub(), cache=_CacheStub(fail_increment=True)
    )

    assert await probe.is_redis_alive() is False
