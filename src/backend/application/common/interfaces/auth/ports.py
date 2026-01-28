from __future__ import annotations

from typing import Protocol

from uuid_utils.compat import UUID

from backend.application.common.exceptions.application import AppError
from backend.application.common.interfaces.auth.types import (
    AuthUser,
    Permission,
    PermissionSpec,
)
from backend.application.handlers.result import Result


class Authenticator(Protocol):
    async def authenticate(
        self: Authenticator, user_id: UUID
    ) -> AuthUser | None: ...

    async def get_permission_for(
        self: Authenticator, user_id: UUID, spec: PermissionSpec
    ) -> Permission: ...


class JwtIssuer(Protocol):
    def issue_access(self: JwtIssuer, *, user_id: UUID) -> str: ...

    def issue_refresh(
        self: JwtIssuer, *, user_id: UUID, fingerprint: str
    ) -> str: ...


class JwtVerifier(Protocol):
    def verify_access(
        self: JwtVerifier, token: str
    ) -> Result[UUID, AppError]: ...

    def verify_refresh(
        self: JwtVerifier, token: str
    ) -> Result[tuple[UUID, str], AppError]: ...


class RefreshStore(Protocol):
    async def rotate(
        self: RefreshStore,
        *,
        user_id: UUID,
        fingerprint: str,
        old: str,
        new: str,
    ) -> None: ...

    async def revoke(
        self: RefreshStore, *, user_id: UUID, fingerprint: str
    ) -> None: ...
