from __future__ import annotations

from typing import Annotated, Final

from pydantic import StringConstraints, field_validator

from backend.domain.core.value_objects.identity.email import Email
from backend.presentation.http.api.schemas.base import BaseShema
from backend.presentation.http.api.schemas.users import UserCreateRequest

_MIN_FINGERPRINT_LENGTH: Final[int] = 8
_MAX_FINGERPRINT_LENGTH: Final[int] = 128
_MAX_LOGIN_PASSWORD_LENGTH: Final[int] = 128
_LOGIN_FINGERPRINT_PATTERN: Final[str] = r"^[A-Za-z0-9._:-]+$"

type LoginEmailStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)
]
type LoginPasswordStr = Annotated[
    str, StringConstraints(min_length=1, max_length=_MAX_LOGIN_PASSWORD_LENGTH)
]
type FingerprintStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=_MIN_FINGERPRINT_LENGTH,
        max_length=_MAX_FINGERPRINT_LENGTH,
        pattern=_LOGIN_FINGERPRINT_PATTERN,
    ),
]


class LoginRequest(BaseShema):
    email: LoginEmailStr
    raw_password: LoginPasswordStr
    fingerprint: FingerprintStr

    @field_validator("email")
    @classmethod
    def _validate_email(cls: type[LoginRequest], value: str) -> str:
        Email(value)
        return value


class RegisterRequest(UserCreateRequest):
    fingerprint: FingerprintStr


class RefreshRequest(BaseShema):
    refresh_token: str
    fingerprint: FingerprintStr


class LogoutRequest(BaseShema):
    refresh_token: str
    fingerprint: FingerprintStr


class TokenPairResponse(BaseShema):
    access_token: str
    refresh_token: str


class SuccessResponse(BaseShema):
    success: bool
