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
from backend.domain.core.value_objects.access.permission_code import (
    PermissionCode,
)
from backend.domain.core.value_objects.access.role_code import RoleCode

_SUPER_ADMIN_ROLE: RoleCode = RoleCode("super_admin")
_ADMIN_ROLE: RoleCode = RoleCode("admin")


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
    ) -> tuple[str, str]: ...


class JwtVerifier(Protocol):
    def verify_access(
        self: JwtVerifier, token: str
    ) -> Result[UUID, AppError]: ...

    def verify_refresh(
        self: JwtVerifier, token: str
    ) -> Result[tuple[UUID, str, str], AppError]: ...


class RefreshStore(Protocol):
    async def get(
        self: RefreshStore, *, user_id: UUID, fingerprint: str
    ) -> str | None: ...

    async def set(
        self: RefreshStore,
        *,
        user_id: UUID,
        fingerprint: str,
        value: str,
        ttl_s: int | None = None,
    ) -> None: ...

    async def delete(
        self: RefreshStore, *, user_id: UUID, fingerprint: str
    ) -> None: ...


def derive_auth_flags(
    role_codes: frozenset[RoleCode],
) -> tuple[bool, bool]:
    is_superuser = _SUPER_ADMIN_ROLE in role_codes
    is_admin = is_superuser or _ADMIN_ROLE in role_codes
    return is_admin, is_superuser


def has_permission(
    permission_codes: frozenset[PermissionCode],
    code: PermissionCode,
) -> bool:
    return code in permission_codes
