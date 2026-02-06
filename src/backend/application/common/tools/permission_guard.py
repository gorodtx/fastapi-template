from __future__ import annotations

from dataclasses import dataclass

from backend.application.common.exceptions.application import (
    AuthorizationError,
)
from backend.application.common.interfaces.auth.types import AuthUser
from backend.domain.core.services.access_control import is_allowed
from backend.domain.core.value_objects.access.permission_code import (
    PermissionCode,
)


@dataclass(slots=True)
class PermissionGuard:
    async def require(self, user: AuthUser, code: PermissionCode) -> None:
        if user.is_superuser:
            return
        allowed = is_allowed(user.roles, code)
        if not allowed:
            raise AuthorizationError(
                f"Access denied by policy for {code.value}"
            )
