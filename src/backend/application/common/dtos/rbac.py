from __future__ import annotations

from uuid_utils.compat import UUID

from backend.application.common.dtos.base import dto
from backend.application.common.dtos.users import UserResponseDTO


@dto
class RoleAssignmentResultDTO:
    user_id: UUID
    role: str


@dto
class AssignRoleToUserDTO:
    user_id: UUID
    role: str
    actor_id: UUID


@dto
class RevokeRoleFromUserDTO:
    user_id: UUID
    role: str
    actor_id: UUID


@dto
class GetUserRolesDTO:
    user_id: UUID


@dto
class UserRolesResponseDTO:
    user_id: UUID
    roles: list[str]
    permissions: list[str]


@dto
class GetUsersByRoleDTO:
    role: str


@dto
class UsersByRoleResponseDTO:
    role: str
    users: list[UserResponseDTO]
