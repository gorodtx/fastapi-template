from __future__ import annotations

import re

from fastapi_backend.domain.core.value_objects.base import ValueObject, value_object


def _validate_password_hash(pwd: Password) -> None:
    """Validate password hash (PHC string format)."""
    val = pwd.value
    if not isinstance(val, str):
        raise TypeError("Password.value must be str")

    if not re.match(r"^\$[a-z0-9-]+\$", val):
        raise ValueError(
            "Invalid password hash format. Expected PHC string "
            "(e.g., $argon2id$v=19$m=65536,t=3,p=4$salt$hash)"
        )

    if len(val) < 20:
        raise ValueError("Password hash too short")


@value_object(_validate_password_hash)
class Password(ValueObject):
    """Password Value Object storing ONLY hashed password.

    Domain layer never sees raw password.
    Application layer hashes before creating this VO."""

    value: str
