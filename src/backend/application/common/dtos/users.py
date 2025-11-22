from __future__ import annotations

from uuid import UUID

from backend.application.common.dtos.base import DTO, dto


@dto
class UserResponseDTO(DTO):
    id: UUID
    email: str
    is_active: bool


@dto
class UserCreateDTO(DTO):
    email: str
    login: str
    username: str
    raw_password: str


@dto
class UserUpdateDTO(DTO):
    user_id: UUID
    email: str | None = None
    raw_password: str | None = None


@dto
class DeleteUserDTO(DTO):
    user_id: UUID


@dto
class GetUserDTO(DTO):
    user_id: UUID
