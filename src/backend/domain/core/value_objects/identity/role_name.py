from __future__ import annotations

import re
from typing import Final

from backend.domain.core.value_objects.base import ValueObject, value_object

_MIN_ROLE_NAME_LENGTH: Final[int] = 2
_MAX_ROLE_NAME_LENGTH: Final[int] = 16


def _validate_role_name(v: RoleName) -> None:
    if not isinstance(v.value, str):
        raise TypeError("RoleName.value must be str")

    if not (_MIN_ROLE_NAME_LENGTH <= len(v.value) <= _MAX_ROLE_NAME_LENGTH):
        raise ValueError(
            f"Role name must be {_MIN_ROLE_NAME_LENGTH}-{_MAX_ROLE_NAME_LENGTH} characters"
        )
    if not re.fullmatch(r"[a-z0-9_]+", v.value):
        raise ValueError("Role name must match [a-z0-9_]+")


@value_object(_validate_role_name)
class RoleName(ValueObject):
    value: str
