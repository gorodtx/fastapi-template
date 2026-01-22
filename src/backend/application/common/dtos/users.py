from __future__ import annotations

from uuid_utils.compat import UUID

from backend.application.common.dtos.base import dto


@dto
class UserResponseDTO:
    id: UUID
    email: str
    login: str
    username: str


@dto
class UserCreateDTO:
    email: str
    login: str
    username: str
    raw_password: str


@dto
class UserUpdateDTO:
    user_id: UUID
    email: str | None = None
    raw_password: str | None = None


@dto
class DeleteUserDTO:
    user_id: UUID


@dto
class GetUserDTO:
    user_id: UUID


@dto
class GetUserWithRolesDTO:
    user_id: UUID


@dto
class UserWithRolesDTO:
    id: UUID
    email: str
    login: str
    username: str
    roles: list[str]
    permissions: list[str]
