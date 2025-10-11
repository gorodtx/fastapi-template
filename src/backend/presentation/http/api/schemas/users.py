from datetime import datetime

from pydantic import BaseModel, EmailStr

from backend.domain.core.entities.base import TypeID


class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str


class UserResponse(BaseModel):
    id: TypeID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
