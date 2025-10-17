from datetime import datetime

from fastapi_backend.application.common.dtos.base_dto import DTO
from fastapi_backend.domain.core.entities.base import TypeID


class UserCreateDTO(DTO):
    email: str
    phone: str


class UserResponseDTO(DTO):
    id: TypeID
    email: str
    phone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdateDTO(DTO):
    email: str | None = None
    phone: str | None = None
