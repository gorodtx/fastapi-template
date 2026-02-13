from __future__ import annotations

from typing import Final

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.types.rbac import (
    PermissionCode,
)

_EMPTY_PERMISSIONS: Final[frozenset[PermissionCode]] = frozenset()
ADMIN_PERMISSIONS: Final[frozenset[PermissionCode]] = frozenset(
    {
        PermissionCode.USERS_READ,
        PermissionCode.USERS_CREATE,
        PermissionCode.USERS_UPDATE,
        PermissionCode.USERS_DELETE,
        PermissionCode.RBAC_READ_ROLES,
        PermissionCode.RBAC_ASSIGN_ROLE,
        PermissionCode.RBAC_REVOKE_ROLE,
    }
)
SUPER_ADMIN_PERMISSIONS: Final[frozenset[PermissionCode]] = ADMIN_PERMISSIONS
# super_admin can be extended later by widening SUPER_ADMIN_PERMISSIONS.

ROLE_PERMISSIONS: Final[dict[SystemRole, frozenset[PermissionCode]]] = {
    SystemRole.USER: _EMPTY_PERMISSIONS,
    SystemRole.ADMIN: ADMIN_PERMISSIONS,
    SystemRole.SUPER_ADMIN: SUPER_ADMIN_PERMISSIONS,
}
