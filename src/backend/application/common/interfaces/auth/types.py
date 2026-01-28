from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.value_objects.access.permission_code import (
    PermissionCode,
)


@dataclass(frozen=True, slots=True)
class AuthUser:
    id: UUID
    roles: frozenset[SystemRole]
    is_active: bool
    is_superuser: bool = False
    email: str | None = None


@dataclass(frozen=True, slots=True)
class PermissionSpec:
    code: PermissionCode
    request_keys: frozenset[str] = frozenset()
    deny_fields: frozenset[str] = frozenset()
    allow_all_fields: bool = True


@dataclass(frozen=True, slots=True)
class Permission:
    allowed: bool
    deny_fields: frozenset[str] = frozenset()
    allow_all_fields: bool = True

    def check(self: Permission, spec: PermissionSpec) -> None:
        if not self.allowed:
            raise PermissionError(f"Forbidden: {spec.code.value}")
        if self.allow_all_fields:
            return
        forbidden = spec.request_keys & self.deny_fields
        if forbidden:
            raise PermissionError(f"Forbidden fields: {sorted(forbidden)}")
