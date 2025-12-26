from __future__ import annotations

import re

from backend.domain.core.value_objects.base import ValueObject, value_object


def validate_email(email: Email) -> None:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email.value):
        raise ValueError(f"Invalid email format: {email.value}")


@value_object(validator=validate_email)
class Email(ValueObject):
    value: str
