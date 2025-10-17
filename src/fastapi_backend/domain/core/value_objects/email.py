from __future__ import annotations

import re

from fastapi_backend.domain.core.value_objects.base import ValueObject, value_object


def validate_email(email: Email) -> None:
    if not isinstance(email.value, str):
        raise TypeError("Email.value must be str")
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email.value):
        raise ValueError(f"Invalid email format: {email.value}")


@value_object(validate_email)
class Email(ValueObject):
    value: str
