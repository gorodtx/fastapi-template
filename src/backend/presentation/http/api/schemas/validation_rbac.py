from __future__ import annotations

import re
from typing import Final

MIN_ROLE_CODE_LENGTH: Final[int] = 3
MAX_ROLE_CODE_LENGTH: Final[int] = 64
ROLE_CODE_PATTERN: Final[str] = r"^[a-z][a-z0-9_]{2,63}$"
_ROLE_CODE_REGEX: Final[re.Pattern[str]] = re.compile(ROLE_CODE_PATTERN)


def validate_role_code(value: str) -> str:
    if not (MIN_ROLE_CODE_LENGTH <= len(value) <= MAX_ROLE_CODE_LENGTH):
        raise ValueError(
            "Role code must be "
            f"{MIN_ROLE_CODE_LENGTH}-{MAX_ROLE_CODE_LENGTH} characters"
        )
    if _ROLE_CODE_REGEX.fullmatch(value) is None:
        raise ValueError(f"Invalid role code format: {value!r}")
    return value
