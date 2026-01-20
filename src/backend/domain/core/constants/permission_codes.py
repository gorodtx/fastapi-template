from __future__ import annotations

from backend.domain.core.value_objects.access.permission_code import PermissionCode

USERS_READ = PermissionCode.USERS_READ
USERS_CREATE = PermissionCode.USERS_CREATE
USERS_UPDATE = PermissionCode.USERS_UPDATE
USERS_DELETE = PermissionCode.USERS_DELETE

RBAC_READ_ROLES = PermissionCode.RBAC_READ_ROLES
RBAC_ASSIGN_ROLE = PermissionCode.RBAC_ASSIGN_ROLE
RBAC_REVOKE_ROLE = PermissionCode.RBAC_REVOKE_ROLE

ALL_PERMISSION_CODES = frozenset(
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
