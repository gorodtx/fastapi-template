from __future__ import annotations

import re
from typing import Final

_ROLE_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9_]{2,63}$"
)


def normalize_role_code(value: str) -> str:
    return value


def validate_role_code(value: str) -> str:
    if _ROLE_CODE_PATTERN.fullmatch(value) is None:
        raise ValueError(f"Invalid role code format: {value!r}")
    return value
