from __future__ import annotations

from collections.abc import Iterable, Set

from backend.domain.core.constants.rbac import RoleAction, SystemRole
from backend.domain.core.constants.rbac_registry import ROLE_PERMISSIONS
from backend.domain.core.exceptions.rbac import RoleHierarchyViolationError
from backend.domain.core.value_objects.access.permission_code import PermissionCode

_EMPTY_PERMISSIONS: frozenset[PermissionCode] = frozenset[PermissionCode]()


def permissions_for_roles(roles: Iterable[SystemRole]) -> frozenset[PermissionCode]:
    permissions: set[PermissionCode] = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS.get(role, _EMPTY_PERMISSIONS))
    return frozenset(permissions)


def is_allowed(roles: Iterable[SystemRole], permission: PermissionCode) -> bool:
    return permission in permissions_for_roles(roles)


def ensure_can_assign_role(actor_roles: Set[SystemRole], target_role: SystemRole) -> None:
    if _can_manage_role(actor_roles, target_role):
        return
    raise RoleHierarchyViolationError(action=RoleAction.ASSIGN, target_role=target_role)


def ensure_can_revoke_role(actor_roles: Set[SystemRole], target_role: SystemRole) -> None:
    if _can_manage_role(actor_roles, target_role):
        return
    raise RoleHierarchyViolationError(action=RoleAction.REVOKE, target_role=target_role)


def _can_manage_role(actor_roles: Set[SystemRole], target_role: SystemRole) -> bool:
    if SystemRole.SUPER_ADMIN in actor_roles:
        return True
    return bool(SystemRole.ADMIN in actor_roles and target_role == SystemRole.USER)
