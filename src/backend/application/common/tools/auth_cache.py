from __future__ import annotations

from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.application.common.interfaces.ports.cache import StrCache


@dataclass(slots=True)
class AuthCacheInvalidator:
    cache: StrCache

    async def invalidate_user(self, user_id: UUID) -> None:
        try:
            await self.cache.delete(f"auth:user:{user_id}")
        except Exception:
            return
