from __future__ import annotations

from typing import Protocol

from backend.application.common.exceptions.application import AppError
from backend.application.common.interfaces.auth.types import (
    AuthUser,
    Permission,
    PermissionSpec,
    UserId,
)
from backend.application.handlers.result import Result


class Authenticator(Protocol):
    async def authenticate(self, user_id: UserId) -> AuthUser | None: ...

    async def get_permission_for(self, user_id: UserId, spec: PermissionSpec) -> Permission: ...


class JwtIssuer(Protocol):
    def issue_access(self, *, user_id: UserId) -> str: ...

    def issue_refresh(self, *, user_id: UserId, fingerprint: str) -> str: ...


class JwtVerifier(Protocol):
    def verify_access(self, token: str) -> Result[UserId, AppError]: ...

    def verify_refresh(self, token: str) -> Result[tuple[UserId, str], AppError]: ...


class RefreshStore(Protocol):
    async def rotate(self, *, user_id: UserId, fingerprint: str, old: str, new: str) -> None: ...

    async def revoke(self, *, user_id: UserId, fingerprint: str) -> None: ...
