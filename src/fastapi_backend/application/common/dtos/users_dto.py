from fastapi_backend.application.common.dtos.base_dto import DTO
from fastapi_backend.domain.core.entities.base import TypeID


class UserResponseDTO(DTO):
    id: TypeID
    email: str
    is_active: bool


class UserCreateDTO(DTO):
    email: str
    login: str
    username: str
    raw_password: str


class UserUpdateDTO(DTO):
    user_id: str
    email: str | None = None
    raw_password: str | None = None


class DeleteUserDTO(DTO):
    user_id: str


class GetUserDTO(DTO):
    user_id: str
