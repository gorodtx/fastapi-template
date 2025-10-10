from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID


class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str


class UserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
