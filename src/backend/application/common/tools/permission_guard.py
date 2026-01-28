from __future__ import annotations

from dataclasses import dataclass

from backend.application.common.exceptions.application import (
    AuthorizationError,
)
from backend.application.common.interfaces.auth.types import AuthUser
from backend.application.common.interfaces.ports.cache import StrCache
from backend.domain.core.services.access_control import is_allowed
from backend.domain.core.value_objects.access.permission_code import (
    PermissionCode,
)

_AUTH_PERMISSION_CACHE_TTL_S: int = 30


def _perm_cache_key(user_id: object, code: PermissionCode) -> str:
    return f"auth:perm:{user_id}:{code.value}"


@dataclass(slots=True)
class PermissionGuard:
    cache: StrCache

    async def require(self, user: AuthUser, code: PermissionCode) -> None:
        if user.is_superuser:
            return
        cache_key = _perm_cache_key(user.id, code)
        cached = await self.cache.get(cache_key)
        if cached is None:
            allowed = is_allowed(user.roles, code)
            await self.cache.set(
                cache_key,
                "1" if allowed else "0",
                ttl_s=_AUTH_PERMISSION_CACHE_TTL_S,
            )
        else:
            allowed = cached == "1"
        if not allowed:
            raise AuthorizationError(
                f"Access denied by policy for {code.value}"
            )
