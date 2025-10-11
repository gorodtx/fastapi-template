from __future__ import annotations

from backend.domain.core.value_objects.base import ValueObject, value_object


def validate_login(login: Login) -> None:
    if not isinstance(login.value, str):
        raise TypeError("Login.value must be str")
    if not (3 <= len(login.value) <= 30):
        raise ValueError("Login must be 3–30 characters")
    if not login.value.isalnum():
        raise ValueError("Login must be alphanumeric")


@value_object(validate_login)
class Login(ValueObject):
    value: str
