from __future__ import annotations

from uuid_utils.compat import UUID

from backend.application.common.dtos.base import DTO, dto


@dto
class UserResponseDTO(DTO):
    id: UUID
    email: str
    login: str
    username: str


@dto
class UserCreateDTO(DTO):
    actor_id: UUID
    email: str
    login: str
    username: str
    raw_password: str


@dto
class UserUpdateDTO(DTO):
    actor_id: UUID
    user_id: UUID
    email: str | None = None
    raw_password: str | None = None


@dto
class DeleteUserDTO(DTO):
    actor_id: UUID
    user_id: UUID


@dto
class GetUserDTO(DTO):
    actor_id: UUID
    user_id: UUID


@dto
class GetUserWithRolesDTO(DTO):
    actor_id: UUID
    user_id: UUID


@dto
class UserWithRolesDTO(DTO):
    id: UUID
    email: str
    login: str
    username: str
    roles: list[str]
    permissions: list[str]
