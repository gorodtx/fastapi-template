from __future__ import annotations

from collections.abc import Callable

from uuid_utils.compat import UUID

from backend.application.common.dtos.rbac import (
    RoleAssignmentResultDTO,
    UserRolesResponseDTO,
    UsersByRoleResponseDTO,
)
from backend.application.common.dtos.users import UserResponseDTO
from backend.domain.core.types.rbac import (
    PermissionCode,
    RoleCode,
)


def present_role_assignment(
    user_id: UUID, role: RoleCode
) -> RoleAssignmentResultDTO:
    return RoleAssignmentResultDTO(user_id=user_id, role=role)


def present_role_assignment_from(
    user_id: UUID, role: RoleCode
) -> Callable[[object], RoleAssignmentResultDTO]:
    def presenter(_unused: object) -> RoleAssignmentResultDTO:
        return present_role_assignment(user_id, role)

    return presenter


def present_user_roles(
    *,
    user_id: UUID,
    roles: frozenset[RoleCode],
    permissions: frozenset[PermissionCode],
) -> UserRolesResponseDTO:
    return UserRolesResponseDTO(
        user_id=user_id,
        roles=sorted(role for role in roles),
        permissions=sorted(permission.value for permission in permissions),
    )


def present_users_by_role(
    role: RoleCode, users: list[UserResponseDTO]
) -> UsersByRoleResponseDTO:
    return UsersByRoleResponseDTO(role=role, users=users)


def present_users_by_role_from(
    role: RoleCode, users: list[UserResponseDTO]
) -> Callable[[object], UsersByRoleResponseDTO]:
    def presenter(_unused: object) -> UsersByRoleResponseDTO:
        return present_users_by_role(role, users)

    return presenter
