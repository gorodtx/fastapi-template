from __future__ import annotations

from uuid_utils.compat import UUID

from backend.application.common.dtos.base import dto


@dto
class TokenPairDTO:
    access_token: str
    refresh_token: str


@dto
class RegisterUserDTO:
    email: str
    login: str
    username: str
    raw_password: str
    fingerprint: str


@dto
class LoginUserDTO:
    email: str
    raw_password: str
    fingerprint: str


@dto
class LogoutUserDTO:
    refresh_token: str
    fingerprint: str
    actor_user_id: UUID


@dto
class RefreshUserDTO:
    refresh_token: str
    fingerprint: str


@dto
class SuccessDTO:
    success: bool = True
