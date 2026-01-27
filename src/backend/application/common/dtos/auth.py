from __future__ import annotations

from backend.application.common.dtos.base import dto


@dto
class TokenPairDTO:
    access_token: str
    refresh_token: str


@dto
class LoginUserDTO:
    email: str
    raw_password: str
    fingerprint: str


@dto
class LogoutUserDTO:
    refresh_token: str
    fingerprint: str


@dto
class RefreshUserDTO:
    refresh_token: str
    fingerprint: str


@dto
class SuccessDTO:
    success: bool = True
