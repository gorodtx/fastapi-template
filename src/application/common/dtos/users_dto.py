from uuid import UUID
from datetime import datetime

from src.application.common.dtos.base_dto import DTO



class UserCreateDTO(DTO):
    email: str
    phone: str


class UserResponseDTO(DTO):
    id: UUID
    email: str
    phone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdateDTO(DTO):
    email: str | None = None
    phone: str | None = None
    