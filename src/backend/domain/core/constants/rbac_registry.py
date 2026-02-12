from __future__ import annotations

from typing import Final

from backend.domain.core.constants.permission_codes import (
    RBAC_ASSIGN_ROLE,
    RBAC_READ_ROLES,
    RBAC_REVOKE_ROLE,
    USERS_CREATE,
    USERS_DELETE,
    USERS_READ,
    USERS_UPDATE,
)
from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.types.rbac import (
    PermissionCode,
)

_EMPTY_PERMISSIONS: Final[frozenset[PermissionCode]] = frozenset()

ROLE_PERMISSIONS: Final[dict[SystemRole, frozenset[PermissionCode]]] = {
    SystemRole.USER: _EMPTY_PERMISSIONS,
    SystemRole.ADMIN: frozenset(
        {
            USERS_READ,
            USERS_CREATE,
            USERS_UPDATE,
            USERS_DELETE,
            RBAC_READ_ROLES,
            RBAC_ASSIGN_ROLE,
            RBAC_REVOKE_ROLE,
        }
    ),
    SystemRole.SUPER_ADMIN: frozenset(
        {
            USERS_READ,
            USERS_CREATE,
            USERS_UPDATE,
            USERS_DELETE,
            RBAC_READ_ROLES,
            RBAC_ASSIGN_ROLE,
            RBAC_REVOKE_ROLE,
        }
    ),
}
