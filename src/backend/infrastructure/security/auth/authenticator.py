from __future__ import annotations

from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.application.common.interfaces.auth.ports import Authenticator
from backend.application.common.interfaces.auth.types import (
    AuthUser,
    Permission,
    PermissionSpec,
)
from backend.application.common.interfaces.ports.persistence.rbac_adapter import (
    RbacAdapter,
)
from backend.application.common.interfaces.ports.persistence.users_adapter import (
    UsersAdapter,
)
from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.constants.rbac_registry import ROLE_PERMISSIONS
from backend.domain.core.value_objects.access.permission_code import (
    PermissionCode,
)


@dataclass(slots=True)
class AuthenticatorImpl(Authenticator):
    users: UsersAdapter
    rbac: RbacAdapter

    async def authenticate(
        self: AuthenticatorImpl, user_id: UUID
    ) -> AuthUser | None:
        result = await self.users.get_by_id(user_id)
        if result.is_err():
            return None
        user = result.unwrap()
        roles = frozenset(user.roles)
        is_superuser = SystemRole.SUPER_ADMIN in roles
        is_admin = is_superuser or SystemRole.ADMIN in roles
        return AuthUser(
            id=user.id,
            roles=roles,
            is_active=user.is_active,
            is_admin=is_admin,
            is_superuser=is_superuser,
            email=user.email.value,
        )

    async def get_permission_for(
        self: AuthenticatorImpl, user_id: UUID, spec: PermissionSpec
    ) -> Permission:
        auth_user = await self.authenticate(user_id)
        if auth_user is None or not auth_user.is_active:
            return Permission(allowed=False)

        if auth_user.is_superuser:
            return Permission(allowed=True)

        allowed_codes: set[PermissionCode] = set()
        for role in auth_user.roles:
            allowed_codes.update(ROLE_PERMISSIONS.get(role, frozenset()))

        allowed = spec.code in allowed_codes
        return Permission(allowed=allowed)
