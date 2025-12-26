from __future__ import annotations

from backend.domain.core.value_objects.access.permission_code import PermissionCode

USERS_READ = PermissionCode("users:read")
USERS_CREATE = PermissionCode("users:create")
USERS_UPDATE = PermissionCode("users:update")
USERS_DELETE = PermissionCode("users:delete")

RBAC_READ_ROLES = PermissionCode("rbac:read_roles")
RBAC_ASSIGN_ROLE = PermissionCode("rbac:assign_role")
RBAC_REVOKE_ROLE = PermissionCode("rbac:revoke_role")

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
