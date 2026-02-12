from __future__ import annotations

from collections.abc import Set

from uuid_utils.compat import UUID

from backend.domain.core.constants.rbac import RoleAction
from backend.domain.core.exceptions.rbac import (
    LastSuperAdminRemovalError,
    RoleHierarchyViolationError,
    RoleSelfModificationError,
)
from backend.domain.core.types.rbac import RoleCode

_SUPER_ADMIN_ROLE: RoleCode = "super_admin"
_ADMIN_ROLE: RoleCode = "admin"
_USER_ROLE: RoleCode = "user"


def ensure_can_assign_role(
    actor_roles: Set[RoleCode], target_role: RoleCode
) -> None:
    if _can_manage_role(actor_roles, target_role):
        return
    raise RoleHierarchyViolationError(
        action=RoleAction.ASSIGN, target_role=target_role
    )


def ensure_can_revoke_role(
    actor_roles: Set[RoleCode], target_role: RoleCode
) -> None:
    if _can_manage_role(actor_roles, target_role):
        return
    raise RoleHierarchyViolationError(
        action=RoleAction.REVOKE, target_role=target_role
    )


def ensure_not_self_role_change(
    *,
    actor_id: UUID,
    target_user_id: UUID,
    action: RoleAction,
) -> None:
    if actor_id == target_user_id:
        raise RoleSelfModificationError(action=action, user_id=actor_id)


def ensure_not_last_super_admin(
    *,
    target_user_id: UUID,
    remaining_super_admins: int,
) -> None:
    if remaining_super_admins <= 0:
        raise LastSuperAdminRemovalError(user_id=target_user_id)


def _can_manage_role(
    actor_roles: Set[RoleCode], target_role: RoleCode
) -> bool:
    if _SUPER_ADMIN_ROLE in actor_roles:
        return True
    return bool(_ADMIN_ROLE in actor_roles and target_role == _USER_ROLE)
