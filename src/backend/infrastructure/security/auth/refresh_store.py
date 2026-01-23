from __future__ import annotations

from dataclasses import dataclass

from backend.application.common.interfaces.auth.ports import RefreshStore
from backend.application.common.interfaces.auth.types import UserId
from backend.application.common.interfaces.ports.cache import StrCache
from backend.application.common.interfaces.ports.shared_lock import SharedLock

AUTH_KEY_PREFIX = "auth:refresh"


def _key(user_id: UserId, fingerprint: str) -> str:
    return f"{AUTH_KEY_PREFIX}:{user_id}:{fingerprint}"


@dataclass(slots=True)
class RefreshStoreImpl(RefreshStore):
    cache: StrCache
    lock: SharedLock

    async def rotate(self, *, user_id: UserId, fingerprint: str, old: str, new: str) -> None:
        key = _key(user_id, fingerprint)
        async with self.lock(key):
            current = await self.cache.get(key)
            if current is not None and current != old:
                await self.cache.delete(key)
                raise PermissionError("Refresh token replay detected")
            await self.cache.set(key, new, ttl_s=30 * 24 * 3600)

    async def revoke(self, *, user_id: UserId, fingerprint: str) -> None:
        await self.cache.delete(_key(user_id, fingerprint))
