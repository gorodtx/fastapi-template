from __future__ import annotations

import re
from typing import Final

from backend.domain.core.value_objects.base import ValueObject, value_object

_ROLE_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9_]{2,63}$"
)


def _validate_role_code(role_code: RoleCode) -> None:
    if _ROLE_CODE_PATTERN.fullmatch(role_code.value) is None:
        raise ValueError(f"Invalid role code format: {role_code.value!r}")


@value_object(validator=_validate_role_code)
class RoleCode(ValueObject):
    value: str
