from __future__ import annotations

from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.domain.core.types.rbac import (
    PermissionCode,
    RoleCode,
)


@dataclass(frozen=True, slots=True)
class AuthUser:
    id: UUID
    role_codes: frozenset[RoleCode]
    permission_codes: frozenset[PermissionCode]
    is_active: bool
    is_admin: bool = False
    is_superuser: bool = False
    email: str | None = None


@dataclass(frozen=True, slots=True)
class PermissionSpec:
    code: PermissionCode


@dataclass(frozen=True, slots=True)
class Permission:
    allowed: bool
