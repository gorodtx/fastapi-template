from __future__ import annotations

import re

from fastapi_backend.domain.core.value_objects.base import ValueObject, value_object


def validate_password(password: Password) -> None:
    val = password.value
    if not isinstance(val, str):
        raise TypeError("Password.value must be str")
    if len(val) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", val):
        raise ValueError("Password must include uppercase letter")
    if not re.search(r"[a-z]", val):
        raise ValueError("Password must include lowercase letter")
    if not re.search(r"\d", val):
        raise ValueError("Password must include digit")
    if not re.search(r"\W", val):
        raise ValueError("Password must include symbol")


@value_object(validate_password)
class Password(ValueObject):
    value: str
