from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from uuid_utils.compat import UUID

from backend.application.common.exceptions.application import ConflictError
from backend.application.common.exceptions.auth import (
    InvalidRefreshTokenError,
    RefreshTokenLockTimeoutError,
    RefreshTokenReplayError,
)
from backend.application.common.exceptions.error_mappers.auth import (
    map_refresh_token_error,
)
from backend.application.common.tools.refresh_tokens import (
    RefreshTokenService,
    refresh_key,
)


class _InMemoryRefreshStore:
    def __init__(self) -> None:
        self._items: dict[str, str] = {}

    async def get(self, *, user_id: UUID, fingerprint: str) -> str | None:
        return self._items.get(refresh_key(user_id, fingerprint))

    async def set(
        self,
        *,
        user_id: UUID,
        fingerprint: str,
        value: str,
        ttl_s: int | None = None,
    ) -> None:
        del ttl_s
        self._items[refresh_key(user_id, fingerprint)] = value

    async def delete(self, *, user_id: UUID, fingerprint: str) -> None:
        self._items.pop(refresh_key(user_id, fingerprint), None)


class _NoopLock:
    @asynccontextmanager
    async def __call__(self, _key: str) -> AsyncIterator[None]:
        yield


class _TimeoutLock:
    @asynccontextmanager
    async def __call__(self, _key: str) -> AsyncIterator[None]:
        raise RefreshTokenLockTimeoutError("lock timeout")
        yield


@pytest.mark.asyncio
async def test_rotate_login_sets_token_when_missing() -> None:
    store = _InMemoryRefreshStore()
    svc = RefreshTokenService(store=store, lock=_NoopLock(), ttl_s=123)

    user_id = UUID("00000000-0000-0000-0000-000000000001")
    await svc.rotate(
        user_id=user_id,
        fingerprint="fp",
        old_jti="",
        new_jti="new-jti",
    )

    assert await store.get(user_id=user_id, fingerprint="fp") == "new-jti"


@pytest.mark.asyncio
async def test_rotate_login_overwrites_existing_token() -> None:
    store = _InMemoryRefreshStore()
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    await store.set(
        user_id=user_id, fingerprint="fp", value="existing", ttl_s=None
    )

    svc = RefreshTokenService(store=store, lock=_NoopLock(), ttl_s=123)
    await svc.rotate(
        user_id=user_id,
        fingerprint="fp",
        old_jti="",
        new_jti="new-jti",
    )

    assert await store.get(user_id=user_id, fingerprint="fp") == "new-jti"


@pytest.mark.asyncio
async def test_rotate_refresh_requires_current_token() -> None:
    store = _InMemoryRefreshStore()
    svc = RefreshTokenService(store=store, lock=_NoopLock(), ttl_s=123)
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    with pytest.raises(InvalidRefreshTokenError):
        await svc.rotate(
            user_id=user_id,
            fingerprint="fp",
            old_jti="old-jti",
            new_jti="new-jti",
        )


@pytest.mark.asyncio
async def test_rotate_refresh_replay_deletes_token() -> None:
    store = _InMemoryRefreshStore()
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    await store.set(
        user_id=user_id, fingerprint="fp", value="current", ttl_s=None
    )

    svc = RefreshTokenService(store=store, lock=_NoopLock(), ttl_s=123)

    with pytest.raises(RefreshTokenReplayError):
        await svc.rotate(
            user_id=user_id,
            fingerprint="fp",
            old_jti="old-jti",
            new_jti="new-jti",
        )

    assert await store.get(user_id=user_id, fingerprint="fp") is None


@pytest.mark.asyncio
async def test_rotate_refresh_success_rotates_token() -> None:
    store = _InMemoryRefreshStore()
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    await store.set(
        user_id=user_id,
        fingerprint="fp",
        value="old-jti",
        ttl_s=None,
    )

    svc = RefreshTokenService(store=store, lock=_NoopLock(), ttl_s=123)
    await svc.rotate(
        user_id=user_id,
        fingerprint="fp",
        old_jti="old-jti",
        new_jti="new-jti",
    )

    assert await store.get(user_id=user_id, fingerprint="fp") == "new-jti"


@pytest.mark.asyncio
async def test_rotate_refresh_lock_timeout_propagates() -> None:
    store = _InMemoryRefreshStore()
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    svc = RefreshTokenService(store=store, lock=_TimeoutLock(), ttl_s=123)

    with pytest.raises(RefreshTokenLockTimeoutError):
        await svc.rotate(
            user_id=user_id,
            fingerprint="fp",
            old_jti="",
            new_jti="new-jti",
        )


def test_refresh_token_error_mapper_handles_lock_timeout() -> None:
    mapped = map_refresh_token_error()(RefreshTokenLockTimeoutError("busy"))

    assert isinstance(mapped, ConflictError)
    assert mapped.message == "Refresh token operation timeout, retry"
