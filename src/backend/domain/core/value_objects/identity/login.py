from __future__ import annotations

from typing import Final

from backend.domain.core.value_objects.base import ValueObject, value_object

_MIN_LOGIN_LENGTH: Final[int] = 3
_MAX_LOGIN_LENGTH: Final[int] = 20


def _validate_login(login: Login) -> None:
    if not isinstance(login.value, str):
        raise TypeError("Login.value must be str")
    if not (_MIN_LOGIN_LENGTH <= len(login.value) <= _MAX_LOGIN_LENGTH):
        raise ValueError(f"Login must be {_MIN_LOGIN_LENGTH}-{_MAX_LOGIN_LENGTH} characters")
    if not login.value.isalnum():
        raise ValueError("Login must be alphanumeric")


@value_object(_validate_login)
class Login(ValueObject):
    value: str
