from __future__ import annotations

from typing import Self

from pydantic import model_validator
from uuid_utils.compat import UUID

from backend.presentation.http.api.schemas.base import BaseSchema
from backend.presentation.http.api.schemas.fields import (
    EmailStr,
    LoginStr,
    RawPasswordStr,
    UsernameStr,
)


class UserCreateRequest(BaseSchema):
    email: EmailStr
    login: LoginStr
    username: UsernameStr
    raw_password: RawPasswordStr


class UserResponse(BaseSchema):
    id: UUID
    email: str
    login: str
    username: str


class UserUpdateRequest(BaseSchema):
    email: EmailStr | None = None
    raw_password: RawPasswordStr | None = None

    @model_validator(mode="after")
    def _validate_not_empty(self: Self) -> Self:
        if self.email is None and self.raw_password is None:
            raise ValueError("At least one field must be provided")
        return self
