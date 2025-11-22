from __future__ import annotations

from uuid import UUID

from backend.application.common.dtos.base import DTO, dto


@dto
class RoleResponseDTO(DTO):
    id: UUID
    name: str
    description: str | None
    permissions: list[str]
    user_count: int


@dto
class RoleCreateDTO(DTO):
    name: str
    description: str | None = None


@dto
class RoleUpdateDTO(DTO):
    role_id: UUID
    name: str | None = None
    description: str | None = None


@dto
class RoleDeleteDTO(DTO):
    role_id: UUID


@dto
class GrantPermissionDTO(DTO):
    role_id: UUID
    permission: str


@dto
class RevokePermissionDTO(DTO):
    role_id: UUID
    permission: str


@dto
class AssignRoleToUserDTO(DTO):
    role_id: UUID
    user_id: UUID


@dto
class RevokeRoleFromUserDTO(DTO):
    role_id: UUID
    user_id: UUID


@dto
class GetRoleDTO(DTO):
    role_id: UUID


@dto
class ListRolesDTO(DTO):
    limit: int = 100
    offset: int = 0


@dto
class ListRolesResponseDTO(DTO):
    roles: list[RoleResponseDTO]
    total: int
    limit: int
    offset: int
