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
from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.constants.rbac_registry import ROLE_PERMISSIONS
from backend.domain.core.value_objects.access.permission_code import (
    PermissionCode,
)


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
    roles: frozenset[SystemRole],
) -> tuple[bool, bool]:
    is_superuser = SystemRole.SUPER_ADMIN in roles
    is_admin = is_superuser or SystemRole.ADMIN in roles
    return is_admin, is_superuser


def is_allowed(roles: frozenset[SystemRole], code: PermissionCode) -> bool:
    if SystemRole.SUPER_ADMIN in roles:
        return True
    allowed_codes: set[PermissionCode] = set()
    for role in roles:
        allowed_codes.update(ROLE_PERMISSIONS.get(role, frozenset()))
    return code in allowed_codes
