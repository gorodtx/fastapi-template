from __future__ import annotations

import re
import unicodedata
from typing import Final

MIN_PASSWORD_LENGTH: Final[int] = 8
MAX_PASSWORD_LENGTH: Final[int] = 64


def normalize_password(raw_password: str) -> str:
    return unicodedata.normalize("NFKC", raw_password)


class RawPasswordValidator:
    _UPPER_RE: Final[re.Pattern[str]] = re.compile(r"[A-Z]")
    _LOWER_RE: Final[re.Pattern[str]] = re.compile(r"[a-z]")
    _DIGIT_RE: Final[re.Pattern[str]] = re.compile(r"\d")
    _SPECIAL_RE: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9]")

    @classmethod
    def validate(cls, raw_password: str) -> str:
        normalized = normalize_password(raw_password)
        if len(normalized) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        if len(normalized) > MAX_PASSWORD_LENGTH:
            raise ValueError(f"Password too long (max {MAX_PASSWORD_LENGTH} characters)")

        if cls._UPPER_RE.search(normalized) is None:
            raise ValueError("Password must contain at least one uppercase letter")
        if cls._LOWER_RE.search(normalized) is None:
            raise ValueError("Password must contain at least one lowercase letter")
        if cls._DIGIT_RE.search(normalized) is None:
            raise ValueError("Password must contain at least one digit")
        if cls._SPECIAL_RE.search(normalized) is None:
            raise ValueError("Password must contain at least one special character")

        return normalized
