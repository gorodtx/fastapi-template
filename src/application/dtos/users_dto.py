from uuid import UUID
from datetime import datetime
from shared.tools.dto import DTO



class UserCreateDTO(DTO):
    first_name: str
    last_name: str
    email: str
    phone: str


class UserResponseDTO(DTO):
    id: UUID
    first_name: str
    last_name: str
    email: str
    phone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdateDTO(DTO):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    