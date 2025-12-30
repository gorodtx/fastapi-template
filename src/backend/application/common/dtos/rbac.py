from __future__ import annotations

from uuid_utils.compat import UUID

from backend.application.common.dtos.base import DTO, dto
from backend.application.common.dtos.users import UserResponseDTO


@dto
class RoleAssignmentResultDTO(DTO):
    user_id: UUID
    role: str


@dto
class AssignRoleToUserDTO(DTO):
    actor_id: UUID
    user_id: UUID
    role: str


@dto
class RevokeRoleFromUserDTO(DTO):
    actor_id: UUID
    user_id: UUID
    role: str


@dto
class GetUserRolesDTO(DTO):
    actor_id: UUID
    user_id: UUID


@dto
class UserRolesResponseDTO(DTO):
    user_id: UUID
    roles: list[str]
    permissions: list[str]


@dto
class GetUsersByRoleDTO(DTO):
    actor_id: UUID
    role: str


@dto
class UsersByRoleResponseDTO(DTO):
    role: str
    users: list[UserResponseDTO]
