from __future__ import annotations

from enum import Enum, unique

RoleCode = str


@unique
class PermissionCode(Enum):
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    RBAC_READ_ROLES = "rbac:read_roles"
    RBAC_ASSIGN_ROLE = "rbac:assign_role"
    RBAC_REVOKE_ROLE = "rbac:revoke_role"


__all__: tuple[str, ...] = (
    "PermissionCode",
    "RoleCode",
)
