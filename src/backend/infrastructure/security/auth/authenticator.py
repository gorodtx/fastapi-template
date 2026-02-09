from __future__ import annotations

from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.application.common.interfaces.auth.ports import (
    Authenticator,
    derive_auth_flags,
    has_permission,
)
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
        permissions_result = await self.rbac.get_user_permission_codes(user_id)
        if permissions_result.is_err():
            return None
        role_codes = frozenset(user.roles)
        permission_codes = frozenset(permissions_result.unwrap())
        is_admin, is_superuser = derive_auth_flags(role_codes)
        return AuthUser(
            id=user.id,
            role_codes=role_codes,
            permission_codes=permission_codes,
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

        allowed = has_permission(auth_user.permission_codes, spec.code)
        return Permission(allowed=allowed)
