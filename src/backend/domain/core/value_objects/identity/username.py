from __future__ import annotations

from typing import Final

from backend.domain.core.value_objects.base import ValueObject, value_object

_MIN_USERNAME_LENGTH: Final[int] = 2
_MAX_USERNAME_LENGTH: Final[int] = 20


def _validate_username(u: Username) -> None:
    val = u.value
    if not (_MIN_USERNAME_LENGTH <= len(val) <= _MAX_USERNAME_LENGTH):
        raise ValueError(
            f"Username must be {_MIN_USERNAME_LENGTH}-{_MAX_USERNAME_LENGTH} characters"
        )
    if not all(c.isprintable() and not c.isspace() for c in val):
        raise ValueError("Username contains invalid characters")


@value_object(validator=_validate_username)
class Username(ValueObject):
    value: str
