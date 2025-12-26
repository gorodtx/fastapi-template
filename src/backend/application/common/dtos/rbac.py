from __future__ import annotations

from uuid import UUID

from backend.application.common.dtos.base import DTO, dto


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
