from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from uuid_utils.compat import UUID

from backend.application.common.interfaces.auth.ports import RefreshStore
from backend.application.common.interfaces.ports.shared_lock import SharedLock

AUTH_REFRESH_PREFIX: Final[str] = "auth:refresh"


def refresh_key(user_id: UUID, fingerprint: str) -> str:
    return f"{AUTH_REFRESH_PREFIX}:{user_id}:{fingerprint}"


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
        old: str,
        new: str,
    ) -> None:
        key = refresh_key(user_id, fingerprint)
        async with self.lock(key):
            current = await self.store.get(
                user_id=user_id, fingerprint=fingerprint
            )
            if current is not None and current != old:
                await self.store.delete(
                    user_id=user_id, fingerprint=fingerprint
                )
                raise PermissionError("Refresh token replay detected")
            await self.store.set(
                user_id=user_id,
                fingerprint=fingerprint,
                value=new,
                ttl_s=self.ttl_s,
            )

    async def revoke(
        self: RefreshTokenService, *, user_id: UUID, fingerprint: str
    ) -> None:
        await self.store.delete(user_id=user_id, fingerprint=fingerprint)
