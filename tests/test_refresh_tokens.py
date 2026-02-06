from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from uuid_utils.compat import UUID

from backend.application.common.exceptions.auth import (
    InvalidRefreshTokenError,
    RefreshTokenReplayError,
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


@pytest.mark.asyncio
async def test_rotate_login_sets_token_when_missing() -> None:
    store = _InMemoryRefreshStore()
    svc = RefreshTokenService(store=store, lock=_NoopLock(), ttl_s=123)

    user_id = UUID("00000000-0000-0000-0000-000000000001")
    await svc.rotate(
        user_id=user_id, fingerprint="fp", old="", new="new-token"
    )

    assert await store.get(user_id=user_id, fingerprint="fp") == "new-token"


@pytest.mark.asyncio
async def test_rotate_login_rejects_existing_token() -> None:
    store = _InMemoryRefreshStore()
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    await store.set(
        user_id=user_id, fingerprint="fp", value="existing", ttl_s=None
    )

    svc = RefreshTokenService(store=store, lock=_NoopLock(), ttl_s=123)

    with pytest.raises(RefreshTokenReplayError):
        await svc.rotate(user_id=user_id, fingerprint="fp", old="", new="new")

    assert await store.get(user_id=user_id, fingerprint="fp") is None


@pytest.mark.asyncio
async def test_rotate_refresh_requires_current_token() -> None:
    store = _InMemoryRefreshStore()
    svc = RefreshTokenService(store=store, lock=_NoopLock(), ttl_s=123)
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    with pytest.raises(InvalidRefreshTokenError):
        await svc.rotate(
            user_id=user_id, fingerprint="fp", old="old", new="new"
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
            user_id=user_id, fingerprint="fp", old="old", new="new"
        )

    assert await store.get(user_id=user_id, fingerprint="fp") is None


@pytest.mark.asyncio
async def test_rotate_refresh_success_rotates_token() -> None:
    store = _InMemoryRefreshStore()
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    await store.set(user_id=user_id, fingerprint="fp", value="old", ttl_s=None)

    svc = RefreshTokenService(store=store, lock=_NoopLock(), ttl_s=123)
    await svc.rotate(user_id=user_id, fingerprint="fp", old="old", new="new")

    assert await store.get(user_id=user_id, fingerprint="fp") == "new"
