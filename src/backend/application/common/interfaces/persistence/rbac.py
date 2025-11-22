from __future__ import annotations

from typing import Protocol

from backend.application.common.dtos.rbac import (
    ListRolesDTO,
    ListRolesResponseDTO,
    RoleResponseDTO,
)
from backend.domain.core.entities.base import TypeID
from backend.domain.core.entities.role import Role
from backend.domain.core.value_objects.access.permission_code import PermissionCode
from backend.domain.core.value_objects.identity.role_name import RoleName


class RbacPort(Protocol):
    async def create_role(self, role: Role) -> RoleResponseDTO: ...

    async def delete_role(self, *, role_id: TypeID) -> RoleResponseDTO: ...

    async def get_role(self, *, role_id: TypeID) -> RoleResponseDTO: ...

    async def list_roles(self, data: ListRolesDTO) -> ListRolesResponseDTO: ...

    async def update_role_name(
        self,
        *,
        role_id: TypeID,
        name: RoleName,
    ) -> RoleResponseDTO: ...

    async def grant_permission(
        self,
        *,
        role_id: TypeID,
        perm: PermissionCode,
    ) -> RoleResponseDTO: ...

    async def revoke_permission(
        self,
        *,
        role_id: TypeID,
        perm: PermissionCode,
    ) -> RoleResponseDTO: ...

    async def assign_role_to_user(
        self,
        *,
        user_id: TypeID,
        role_id: TypeID,
    ) -> RoleResponseDTO: ...

    async def revoke_role_from_user(
        self,
        *,
        user_id: TypeID,
        role_id: TypeID,
    ) -> RoleResponseDTO: ...
