from fastapi_backend.application.common.dtos.base_dto import DTO
from fastapi_backend.domain.core.entities.base import TypeID


class RoleResponseDTO(DTO):
    id: TypeID
    name: str
    description: str | None
    permissions: list[str]
    user_count: int


class RoleCreateDTO(DTO):
    name: str
    description: str | None = None


class RoleUpdateDTO(DTO):
    role_id: str
    name: str | None = None
    description: str | None = None


class RoleDeleteDTO(DTO):
    role_id: str


class GrantPermissionDTO(DTO):
    role_id: str
    permission: str


class RevokePermissionDTO(DTO):
    role_id: str
    permission: str


class AssignRoleToUserDTO(DTO):
    role_id: str
    user_id: str


class RevokeRoleFromUserDTO(DTO):
    role_id: str
    user_id: str


class GetRoleDTO(DTO):
    role_id: str


class ListRolesDTO(DTO):
    limit: int = 100
    offset: int = 0


class ListRolesResponseDTO(DTO):
    roles: list[RoleResponseDTO]
    total: int
    limit: int
    offset: int
