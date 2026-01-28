from __future__ import annotations

from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.value_objects.access.permission_code import (
    PermissionCode,
)


@dataclass(frozen=True, slots=True)
class AuthUser:
    id: UUID
    roles: frozenset[SystemRole]
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
