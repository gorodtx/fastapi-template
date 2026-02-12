from __future__ import annotations

from backend.presentation.http.api.schemas.base import BaseSchema
from backend.presentation.http.api.schemas.fields import (
    EmailStr,
    FingerprintStr,
    LoginPasswordStr,
)
from backend.presentation.http.api.schemas.users import UserCreateRequest


class LoginRequest(BaseSchema):
    email: EmailStr
    raw_password: LoginPasswordStr
    fingerprint: FingerprintStr


class RegisterRequest(UserCreateRequest):
    fingerprint: FingerprintStr


class RefreshRequest(BaseSchema):
    refresh_token: str
    fingerprint: FingerprintStr


class LogoutRequest(BaseSchema):
    refresh_token: str
    fingerprint: FingerprintStr


class TokenPairResponse(BaseSchema):
    access_token: str
    refresh_token: str


class SuccessResponse(BaseSchema):
    success: bool
