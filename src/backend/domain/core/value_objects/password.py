from __future__ import annotations

import re
from typing import Final

from backend.domain.core.value_objects.base import ValueObject, value_object

MIN_HASH_LENGTH: Final[int] = 20
_PHC_PREFIX_RE: Final[re.Pattern[str]] = re.compile(r"^\$[a-z0-9-]+\$")


def _validate_password_hash(pwd: Password) -> None:
    val = pwd.value

    if not _PHC_PREFIX_RE.match(val):
        raise ValueError(
            "Invalid password hash format. Expected PHC-like string "
            "(e.g., $argon2id$v=19$m=65536,t=3,p=4$salt$hash)"
        )

    if len(val) < MIN_HASH_LENGTH:
        raise ValueError("Password hash too short")


@value_object(validator=_validate_password_hash)
class Password(ValueObject):
    value: str
