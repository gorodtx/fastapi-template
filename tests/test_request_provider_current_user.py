from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.requests import Request
from uuid_utils.compat import UUID

from backend.application.common.exceptions.application import (
    AppError,
    UnauthenticatedError,
)
from backend.application.common.interfaces.auth.types import AuthUser
from backend.application.handlers.result import Result, ResultImpl
from backend.domain.core.types.rbac import PermissionCode
from backend.infrastructure.security.auth.cache_codec import encode_cached_user
from backend.presentation.di.request_provider import RequestProvider


def _request_with_auth(token: str) -> Request:
    scope: dict[str, object] = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/users/me",
        "query_string": b"",
        "headers": [
            (b"authorization", f"Bearer {token}".encode()),
        ],
    }
    return Request(scope)


@dataclass(slots=True)
class _CacheStub:
    values: dict[str, str] = field(default_factory=dict)
    set_calls: list[tuple[str, str, int | None]] = field(default_factory=list)

    async def get(self: _CacheStub, key: str) -> str | None:
        return self.values.get(key)

    async def set(
        self: _CacheStub, key: str, value: str, *, ttl_s: int | None = None
    ) -> None:
        self.values[key] = value
        self.set_calls.append((key, value, ttl_s))

    async def delete(self: _CacheStub, key: str) -> None:
        self.values.pop(key, None)

    async def increment(self: _CacheStub, key: str, *, delta: int = 1) -> int:
        raw = self.values.get(key, "0")
        current = int(raw)
        updated = current + delta
        self.values[key] = str(updated)
        return updated


@dataclass(frozen=True, slots=True)
class _JwtVerifierStub:
    user_id: UUID

    def verify_access(
        self: _JwtVerifierStub, token: str
    ) -> Result[UUID, AppError]:
        _ = token
        return ResultImpl.ok(self.user_id, UnauthenticatedError)

    def verify_refresh(
        self: _JwtVerifierStub, token: str
    ) -> Result[tuple[UUID, str, str], AppError]:
        _ = token
        raise NotImplementedError


def _active_auth_user(user_id: UUID) -> AuthUser:
    return AuthUser(
        id=user_id,
        role_codes=frozenset({"user"}),
        permission_codes=frozenset({PermissionCode.USERS_READ}),
        is_active=True,
        is_admin=False,
        is_superuser=False,
        email="user@example.com",
    )


@pytest.mark.asyncio
async def test_current_user_loads_from_cache_without_db_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    cache = _CacheStub()
    cached_user = _active_auth_user(user_id)

    cache.values["auth:user:00000000-0000-0000-0000-000000000001"] = (
        encode_cached_user(cached_user)
    )

    calls = 0

    async def _fake_auth(
        session_factory: async_sessionmaker[AsyncSession],
        requested_user_id: UUID,
    ) -> AuthUser | None:
        nonlocal calls
        _ = session_factory
        _ = requested_user_id
        calls += 1
        return None

    monkeypatch.setattr(
        "backend.presentation.di.request_provider._authenticate_with_fresh_session",
        _fake_auth,
    )

    provider = RequestProvider()
    resolved = await provider.current_user(
        request=_request_with_auth("token"),
        jwt_verifier=_JwtVerifierStub(user_id),
        session_factory=async_sessionmaker[AsyncSession](),
        cache=cache,
        auth_user_cache_ttl_s=300,
    )

    assert resolved == cached_user
    assert calls == 0
    assert cache.set_calls == []


@pytest.mark.asyncio
async def test_current_user_uses_fresh_session_lookup_on_cache_miss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000002")
    cache = _CacheStub()
    loaded_user = _active_auth_user(user_id)
    observed: list[tuple[object, UUID]] = []

    async def _fake_auth(
        session_factory: async_sessionmaker[AsyncSession],
        requested_user_id: UUID,
    ) -> AuthUser | None:
        observed.append((session_factory, requested_user_id))
        return loaded_user

    monkeypatch.setattr(
        "backend.presentation.di.request_provider._authenticate_with_fresh_session",
        _fake_auth,
    )

    provider = RequestProvider()
    session_factory = async_sessionmaker[AsyncSession]()
    resolved = await provider.current_user(
        request=_request_with_auth("token"),
        jwt_verifier=_JwtVerifierStub(user_id),
        session_factory=session_factory,
        cache=cache,
        auth_user_cache_ttl_s=120,
    )

    assert resolved == loaded_user
    assert observed == [(session_factory, user_id)]
    assert len(cache.set_calls) == 1
    assert (
        cache.set_calls[0][0]
        == "auth:user:00000000-0000-0000-0000-000000000002"
    )
    assert cache.set_calls[0][2] == 120
