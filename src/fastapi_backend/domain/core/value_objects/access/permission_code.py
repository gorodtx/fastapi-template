from __future__ import annotations

import re

from fastapi_backend.domain.core.value_objects.base import ValueObject, value_object


def _validate_permission_code(v: PermissionCode) -> None:
    if not isinstance(v.value, str):
        raise TypeError("PermissionCode.value must be str")
    if not re.fullmatch(r"[a-z]+:[a-z_]+", v.value):
        raise ValueError("Permission code must match 'domain:action'")


@value_object(_validate_permission_code)
class PermissionCode(ValueObject):
    value: str
