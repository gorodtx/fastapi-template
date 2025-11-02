from __future__ import annotations

import re
from typing import Final

MIN_PASSWORD_LENGTH: Final[int] = 8
MAX_PASSWORD_LENGTH: Final[int] = 128


class RawPasswordValidator:
    @staticmethod
    def validate(raw_password: str) -> None:
        if len(raw_password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

        if len(raw_password) > MAX_PASSWORD_LENGTH:
            raise ValueError(f"Password too long (max {MAX_PASSWORD_LENGTH} characters)")

        if not re.search(r"[A-Z]", raw_password):
            raise ValueError("Password must include at least one uppercase letter")

        if not re.search(r"[a-z]", raw_password):
            raise ValueError("Password must include at least one lowercase letter")

        if not re.search(r"\d", raw_password):
            raise ValueError("Password must include at least one digit")

        if not re.search(r"[^A-Za-z0-9]", raw_password):
            raise ValueError("Password must include at least one special character")

        if re.search(r"(.)\1{2,}", raw_password):
            raise ValueError("Password contains too many repeated characters")
