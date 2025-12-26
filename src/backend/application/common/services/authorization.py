from __future__ import annotations

from dataclasses import dataclass

from backend.application.common.exceptions.application import PermissionDeniedError
from backend.application.common.interfaces.persistence.rbac import RbacPort
from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.base import TypeID
from backend.domain.core.services.access_control import permissions_for_roles
from backend.domain.core.value_objects.access.permission_code import PermissionCode


@dataclass(frozen=True, slots=True)
class AuthorizationContext:
    user_id: TypeID
    roles: set[SystemRole]
    permissions: frozenset[PermissionCode]


@dataclass(slots=True)
class AuthorizationService:
    async def get_permissions(
        self, *, user_id: TypeID, rbac: RbacPort
    ) -> frozenset[PermissionCode]:
        context = await self.get_context(user_id=user_id, rbac=rbac)
        return context.permissions

    async def has_permission(
        self,
        *,
        user_id: TypeID,
        permission: PermissionCode,
        rbac: RbacPort,
    ) -> bool:
        context = await self.get_context(user_id=user_id, rbac=rbac)
        return permission in context.permissions

    async def require_permission(
        self,
        *,
        user_id: TypeID,
        permission: PermissionCode,
        rbac: RbacPort,
    ) -> AuthorizationContext:
        context = await self.get_context(user_id=user_id, rbac=rbac)
        self.require_permission_in_context(context, permission)
        return context

    async def get_context(self, *, user_id: TypeID, rbac: RbacPort) -> AuthorizationContext:
        roles = await rbac.list_user_roles(user_id=user_id)
        permissions = permissions_for_roles(roles)
        return AuthorizationContext(user_id=user_id, roles=roles, permissions=permissions)

    def require_permission_in_context(
        self,
        context: AuthorizationContext,
        permission: PermissionCode,
    ) -> None:
        if permission not in context.permissions:
            raise PermissionDeniedError(user_id=context.user_id, missing_permission=permission)
