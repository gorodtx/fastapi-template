from __future__ import annotations

import re
from typing import Final

MIN_LOGIN_LENGTH: Final[int] = 3
MAX_LOGIN_LENGTH: Final[int] = 20

_EMAIL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

MIN_USERNAME_LENGTH: Final[int] = 2
MAX_USERNAME_LENGTH: Final[int] = 20

MIN_PASSWORD_HASH_LENGTH: Final[int] = 20
_PASSWORD_HASH_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\$[a-z0-9-]+\$"
)


def normalize_login(value: str) -> str:
    return value


def validate_login(value: str) -> str:
    if not (MIN_LOGIN_LENGTH <= len(value) <= MAX_LOGIN_LENGTH):
        raise ValueError(
            f"Login must be {MIN_LOGIN_LENGTH}-{MAX_LOGIN_LENGTH} characters"
        )
    if not value.isalnum():
        raise ValueError("Login must be alphanumeric")
    return value


def normalize_email(value: str) -> str:
    return value


def validate_email(value: str) -> str:
    if _EMAIL_PATTERN.fullmatch(value) is None:
        raise ValueError(f"Invalid email format: {value}")
    return value


def normalize_username(value: str) -> str:
    return value


def validate_username(value: str) -> str:
    if not (MIN_USERNAME_LENGTH <= len(value) <= MAX_USERNAME_LENGTH):
        raise ValueError(
            f"Username must be {MIN_USERNAME_LENGTH}-{MAX_USERNAME_LENGTH} characters"
        )
    if not all(char.isprintable() and not char.isspace() for char in value):
        raise ValueError("Username contains invalid characters")
    return value


def normalize_password_hash(value: str) -> str:
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
