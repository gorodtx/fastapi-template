from __future__ import annotations

from collections.abc import Callable

from uuid_utils.compat import UUID

from backend.application.common.dtos.rbac import (
    RoleAssignmentResultDTO,
    UserRolesResponseDTO,
    UsersByRoleResponseDTO,
)
from backend.application.common.dtos.users import UserResponseDTO
from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.user import User
from backend.domain.core.services.access_control import permissions_for_roles


def present_role_assignment(
    user_id: UUID, role: SystemRole
) -> RoleAssignmentResultDTO:
    return RoleAssignmentResultDTO(user_id=user_id, role=role.value)


def present_role_assignment_from(
    user_id: UUID, role: SystemRole
) -> Callable[[object], RoleAssignmentResultDTO]:
    def presenter(_unused: object) -> RoleAssignmentResultDTO:
        return present_role_assignment(user_id, role)

    return presenter


def present_user_roles(user: User) -> UserRolesResponseDTO:
    return UserRolesResponseDTO(
        user_id=user.id,
        roles=[role.value for role in user.roles],
        permissions=[perm.value for perm in permissions_for_roles(user.roles)],
    )


def present_users_by_role(
    role: SystemRole, users: list[UserResponseDTO]
) -> UsersByRoleResponseDTO:
    return UsersByRoleResponseDTO(role=role.value, users=users)


def present_users_by_role_from(
    role: SystemRole, users: list[UserResponseDTO]
) -> Callable[[object], UsersByRoleResponseDTO]:
    def presenter(_unused: object) -> UsersByRoleResponseDTO:
        return present_users_by_role(role, users)

    return presenter
