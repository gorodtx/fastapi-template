from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from uuid_utils.compat import UUID

from backend.application.common.exceptions.auth import (
    InvalidRefreshTokenError,
    RefreshTokenReplayError,
)
from backend.application.common.interfaces.auth.ports import RefreshStore
from backend.application.common.interfaces.ports.shared_lock import SharedLock

AUTH_REFRESH_PREFIX: Final[str] = "auth:refresh"


def refresh_key(user_id: UUID, fingerprint: str) -> str:
    return f"{AUTH_REFRESH_PREFIX}:{user_id}:{fingerprint}"


def refresh_lock_key(user_id: UUID, fingerprint: str) -> str:
    # Do not share the same Redis key for both the lock and the refresh token value.
    # Otherwise, token writes/deletes would break lock ownership semantics.
    return f"{refresh_key(user_id, fingerprint)}:lock"


@dataclass(slots=True)
class RefreshTokenService:
    store: RefreshStore
    lock: SharedLock
    ttl_s: int

    async def rotate(
        self: RefreshTokenService,
        *,
        user_id: UUID,
        fingerprint: str,
        old_jti: str,
        new_jti: str,
    ) -> None:
        async with self.lock(refresh_lock_key(user_id, fingerprint)):
            current = await self.store.get(
                user_id=user_id, fingerprint=fingerprint
            )
            if old_jti:
                if current is None:
                    raise InvalidRefreshTokenError("Refresh token not found")
                if current != old_jti:
                    await self.store.delete(
                        user_id=user_id, fingerprint=fingerprint
                    )
                    raise RefreshTokenReplayError(
                        "Refresh token replay detected"
                    )
            await self.store.set(
                user_id=user_id,
                fingerprint=fingerprint,
                value=new_jti,
                ttl_s=self.ttl_s,
            )

    async def revoke(
        self: RefreshTokenService, *, user_id: UUID, fingerprint: str
    ) -> None:
        await self.store.delete(user_id=user_id, fingerprint=fingerprint)
