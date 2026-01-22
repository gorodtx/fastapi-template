from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, ParamSpec, TypeVar

if TYPE_CHECKING:

    class BaseModel:
        def __init__(self, **_data: object) -> None: ...

    _P = ParamSpec("_P")
    _R = TypeVar("_R")

    def field_validator(*_fields: str) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...
else:
    from pydantic import BaseModel, field_validator

from uuid_utils.compat import UUID

from backend.application.common.tools.password_validator import RawPasswordValidator


class UserCreateRequest(BaseModel):
    email: str
    login: str
    username: str
    raw_password: str

    @field_validator("raw_password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        RawPasswordValidator.validate(value)
        return value


class UserResponse(BaseModel):
    id: UUID
    email: str
    login: str
    username: str
