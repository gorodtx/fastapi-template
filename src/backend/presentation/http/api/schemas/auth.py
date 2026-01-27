from __future__ import annotations

from backend.presentation.http.api.schemas.base import BaseShema


class LoginRequest(BaseShema):
    email: str
    raw_password: str
    fingerprint: str


class RefreshRequest(BaseShema):
    refresh_token: str
    fingerprint: str


class LogoutRequest(BaseShema):
    refresh_token: str
    fingerprint: str


class TokenPairResponse(BaseShema):
    access_token: str
    refresh_token: str


class SuccessResponse(BaseShema):
    success: bool
