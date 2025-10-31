from __future__ import annotations

import re

from fastapi_backend.domain.core.value_objects.base import ValueObject, value_object

_RESERVED = {"super_admin", "admin", "user"}


def _validate_role_name(v: RoleName) -> None:
    if not isinstance(v.value, str):
        raise TypeError("RoleName.value must be str")
    if not (2 <= len(v.value) <= 50):
        raise ValueError("Role name must be 2–50 characters")
    if not re.fullmatch(r"[a-z0-9_]+", v.value):
        raise ValueError("Role name must match [a-z0-9_]+")
    if v.value.strip() == "":
        raise ValueError("Role name cannot be empty")


@value_object(_validate_role_name)
class RoleName(ValueObject):
    value: str
