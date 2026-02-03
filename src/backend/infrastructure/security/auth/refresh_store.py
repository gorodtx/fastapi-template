from __future__ import annotations

from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.application.common.interfaces.auth.ports import RefreshStore
from backend.application.common.interfaces.ports.cache import StrCache
from backend.application.common.tools.refresh_tokens import refresh_key


@dataclass(slots=True)
class RefreshStoreImpl(RefreshStore):
    cache: StrCache

    async def get(
        self: RefreshStoreImpl, *, user_id: UUID, fingerprint: str
    ) -> str | None:
        return await self.cache.get(refresh_key(user_id, fingerprint))

    async def set(
        self: RefreshStoreImpl,
        *,
        user_id: UUID,
        fingerprint: str,
        value: str,
        ttl_s: int | None = None,
    ) -> None:
        await self.cache.set(
            refresh_key(user_id, fingerprint),
            value,
            ttl_s=ttl_s,
        )

    async def delete(
        self: RefreshStoreImpl, *, user_id: UUID, fingerprint: str
    ) -> None:
        await self.cache.delete(refresh_key(user_id, fingerprint))
