from __future__ import annotations

from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.application.common.interfaces.ports.cache import StrCache
from backend.domain.core.constants.permission_codes import (
    ALL_PERMISSION_CODES,
)


@dataclass(slots=True)
class AuthCacheInvalidator:
    cache: StrCache

    async def invalidate_user(self, user_id: UUID) -> None:
        await self.cache.delete(f"auth:user:{user_id}")
        for code in ALL_PERMISSION_CODES:
            await self.cache.delete(f"auth:perm:{user_id}:{code.value}")
