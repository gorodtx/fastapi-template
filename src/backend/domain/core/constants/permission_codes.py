from __future__ import annotations

from backend.domain.core.types.rbac import (
    PermissionCode,
)

USERS_READ: PermissionCode = PermissionCode.USERS_READ
USERS_CREATE: PermissionCode = PermissionCode.USERS_CREATE
USERS_UPDATE: PermissionCode = PermissionCode.USERS_UPDATE
USERS_DELETE: PermissionCode = PermissionCode.USERS_DELETE

RBAC_READ_ROLES: PermissionCode = PermissionCode.RBAC_READ_ROLES
RBAC_ASSIGN_ROLE: PermissionCode = PermissionCode.RBAC_ASSIGN_ROLE
RBAC_REVOKE_ROLE: PermissionCode = PermissionCode.RBAC_REVOKE_ROLE

ALL_PERMISSION_CODES: frozenset[PermissionCode] = frozenset(
    {
        USERS_READ,
        USERS_CREATE,
        USERS_UPDATE,
        USERS_DELETE,
        RBAC_READ_ROLES,
        RBAC_ASSIGN_ROLE,
        RBAC_REVOKE_ROLE,
    }
)
