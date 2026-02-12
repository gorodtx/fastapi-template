from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, StringConstraints

from backend.application.common.tools.password_validator import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    RawPasswordValidator,
)
from backend.domain.core.policies.identity import (
    FINGERPRINT_PATTERN,
    MAX_EMAIL_LENGTH,
    MAX_FINGERPRINT_LENGTH,
    MAX_LOGIN_LENGTH,
    MAX_LOGIN_PASSWORD_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_EMAIL_LENGTH,
    MIN_FINGERPRINT_LENGTH,
    MIN_LOGIN_LENGTH,
    MIN_LOGIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
    validate_email,
    validate_fingerprint,
    validate_login,
    validate_username,
)


def _validate_email(value: str) -> str:
    return validate_email(value)


def _validate_login(value: str) -> str:
    return validate_login(value)


def _validate_username(value: str) -> str:
    return validate_username(value)


def _validate_fingerprint(value: str) -> str:
    return validate_fingerprint(value)


def _validate_raw_password(value: str) -> str:
    return RawPasswordValidator.validate(raw_password=value)


type EmailStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=MIN_EMAIL_LENGTH,
        max_length=MAX_EMAIL_LENGTH,
    ),
    AfterValidator(_validate_email),
]
type LoginStr = Annotated[
    str,
    StringConstraints(
        min_length=MIN_LOGIN_LENGTH,
        max_length=MAX_LOGIN_LENGTH,
    ),
    AfterValidator(_validate_login),
]
type UsernameStr = Annotated[
    str,
    StringConstraints(
        min_length=MIN_USERNAME_LENGTH,
        max_length=MAX_USERNAME_LENGTH,
    ),
    AfterValidator(_validate_username),
]
type RawPasswordStr = Annotated[
    str,
    StringConstraints(
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
    ),
    AfterValidator(_validate_raw_password),
]
type LoginPasswordStr = Annotated[
    str,
    StringConstraints(
        min_length=MIN_LOGIN_PASSWORD_LENGTH,
        max_length=MAX_LOGIN_PASSWORD_LENGTH,
    ),
]
type FingerprintStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=MIN_FINGERPRINT_LENGTH,
        max_length=MAX_FINGERPRINT_LENGTH,
        pattern=FINGERPRINT_PATTERN,
    ),
    AfterValidator(_validate_fingerprint),
]
