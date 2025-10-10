from __future__ import annotations

from backend.domain.core.value_objects.base import value_object, ValueObject


def validate_username(username: "Username") -> None:  # forward reference
    val = username.value
    if not isinstance(val, str):
        raise TypeError("Username.value must be str")
    if not (2 <= len(val) <= 50):
        raise ValueError("Username must be 2–50 characters")
    if not all(c.isprintable() and not c.isspace() for c in val):
        raise ValueError("Username contains invalid characters")


@value_object(validate=validate_username)
class Username(ValueObject):
    value: str
