from __future__ import annotations

import re
import unicodedata
from typing import Final

MIN_EMAIL_LENGTH: Final[int] = 3
MAX_EMAIL_LENGTH: Final[int] = 255

MIN_LOGIN_LENGTH: Final[int] = 3
MAX_LOGIN_LENGTH: Final[int] = 20

MIN_LOGIN_PASSWORD_LENGTH: Final[int] = 1
MAX_LOGIN_PASSWORD_LENGTH: Final[int] = 128

MIN_FINGERPRINT_LENGTH: Final[int] = 8
MAX_FINGERPRINT_LENGTH: Final[int] = 128
FINGERPRINT_PATTERN: Final[str] = r"^[A-Za-z0-9._:-]+$"
_FINGERPRINT_REGEX: Final[re.Pattern[str]] = re.compile(FINGERPRINT_PATTERN)

_EMAIL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

MIN_USERNAME_LENGTH: Final[int] = 2
MAX_USERNAME_LENGTH: Final[int] = 20

MIN_PASSWORD_HASH_LENGTH: Final[int] = 20
_PASSWORD_HASH_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\$[a-z0-9-]+\$"
)

MIN_PASSWORD_LENGTH: Final[int] = 8
MAX_PASSWORD_LENGTH: Final[int] = 64


def validate_login(value: str) -> str:
    if not (MIN_LOGIN_LENGTH <= len(value) <= MAX_LOGIN_LENGTH):
        raise ValueError(
            f"Login must be {MIN_LOGIN_LENGTH}-{MAX_LOGIN_LENGTH} characters"
        )
    if not value.isalnum():
        raise ValueError("Login must be alphanumeric")
    return value


def validate_email(value: str) -> str:
    if not (MIN_EMAIL_LENGTH <= len(value) <= MAX_EMAIL_LENGTH):
        raise ValueError(
            f"Email must be {MIN_EMAIL_LENGTH}-{MAX_EMAIL_LENGTH} characters"
        )
    if _EMAIL_PATTERN.fullmatch(value) is None:
        raise ValueError(f"Invalid email format: {value}")
    return value


def validate_username(value: str) -> str:
    if not (MIN_USERNAME_LENGTH <= len(value) <= MAX_USERNAME_LENGTH):
        raise ValueError(
            f"Username must be {MIN_USERNAME_LENGTH}-{MAX_USERNAME_LENGTH} characters"
        )
    if not all(char.isprintable() and not char.isspace() for char in value):
        raise ValueError("Username contains invalid characters")
    return value


def validate_fingerprint(value: str) -> str:
    if not (MIN_FINGERPRINT_LENGTH <= len(value) <= MAX_FINGERPRINT_LENGTH):
        raise ValueError(
            "Fingerprint must be "
            f"{MIN_FINGERPRINT_LENGTH}-{MAX_FINGERPRINT_LENGTH} characters"
        )
    if _FINGERPRINT_REGEX.fullmatch(value) is None:
        raise ValueError("Fingerprint contains invalid characters")
    return value


def validate_password_hash(value: str) -> str:
    if _PASSWORD_HASH_PREFIX_PATTERN.match(value) is None:
        raise ValueError(
            "Invalid password hash format. Expected PHC-like string "
            "(e.g., $argon2id$v=19$m=65536,t=3,p=4$salt$hash)"
        )
    if len(value) < MIN_PASSWORD_HASH_LENGTH:
        raise ValueError("Password hash too short")
    return value


def normalize_password(raw_password: str) -> str:
    return unicodedata.normalize("NFKC", raw_password)


class RawPasswordValidator:
    _UPPER_RE: Final[re.Pattern[str]] = re.compile(r"[A-Z]")
    _LOWER_RE: Final[re.Pattern[str]] = re.compile(r"[a-z]")
    _DIGIT_RE: Final[re.Pattern[str]] = re.compile(r"\d")
    _SPECIAL_RE: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9]")

    @classmethod
    def validate(cls: type[RawPasswordValidator], raw_password: str) -> str:
        normalized = normalize_password(raw_password)
        if len(normalized) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
            )
        if len(normalized) > MAX_PASSWORD_LENGTH:
            raise ValueError(
                f"Password too long (max {MAX_PASSWORD_LENGTH} characters)"
            )

        if cls._UPPER_RE.search(normalized) is None:
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )
        if cls._LOWER_RE.search(normalized) is None:
            raise ValueError(
                "Password must contain at least one lowercase letter"
            )
        if cls._DIGIT_RE.search(normalized) is None:
            raise ValueError("Password must contain at least one digit")
        if cls._SPECIAL_RE.search(normalized) is None:
            raise ValueError(
                "Password must contain at least one special character"
            )

        return normalized
