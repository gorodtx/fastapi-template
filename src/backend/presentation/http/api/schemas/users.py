from __future__ import annotations

from typing import Annotated, Self

from pydantic import StringConstraints, field_validator, model_validator
from uuid_utils.compat import UUID

from backend.application.common.tools.password_validator import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    RawPasswordValidator,
)
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.presentation.http.api.schemas.base import BaseShema

type EmailStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)
]
type LoginStr = Annotated[str, StringConstraints(min_length=3, max_length=20)]
type UsernameStr = Annotated[
    str, StringConstraints(min_length=2, max_length=20)
]
type RawPasswordStr = Annotated[
    str,
    StringConstraints(
        min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH
    ),
]


class UserCreateRequest(BaseShema):
    email: EmailStr
    login: LoginStr
    username: UsernameStr
    raw_password: RawPasswordStr

    @field_validator("email")
    @classmethod
    def _validate_email(cls: type[UserCreateRequest], value: str) -> str:
        Email(value)
        return value

    @field_validator("login")
    @classmethod
    def _validate_login(cls: type[UserCreateRequest], value: str) -> str:
        Login(value)
        return value

    @field_validator("username")
    @classmethod
    def _validate_username(cls: type[UserCreateRequest], value: str) -> str:
        Username(value)
        return value

    @field_validator("raw_password")
    @classmethod
    def _validate_password(cls: type[UserCreateRequest], value: str) -> str:
        RawPasswordValidator.validate(raw_password=value)
        return value


class UserResponse(BaseShema):
    id: UUID
    email: str
    login: str
    username: str


class UserUpdateRequest(BaseShema):
    email: EmailStr | None = None
    raw_password: RawPasswordStr | None = None

    @model_validator(mode="after")
    def _validate_not_empty(self: Self) -> Self:
        if self.email is None and self.raw_password is None:
            raise ValueError("At least one field must be provided")
        return self

    @field_validator("email")
    @classmethod
    def _validate_email(
        cls: type[UserUpdateRequest], value: str | None
    ) -> str | None:
        if value is None:
            return None
        Email(value)
        return value

    @field_validator("raw_password")
    @classmethod
    def _validate_password(
        cls: type[UserUpdateRequest], value: str | None
    ) -> str | None:
        if value is None:
            return None
        RawPasswordValidator.validate(raw_password=value)
        return value
