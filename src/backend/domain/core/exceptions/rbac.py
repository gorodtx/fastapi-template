from __future__ import annotations

from uuid_utils.compat import UUID

from backend.domain.core.constants.rbac import RoleAction, SystemRole
from backend.domain.core.exceptions.base import DomainError


class RoleError(DomainError):
    """Base role domain error."""

    __slots__ = ()


class RoleAssignmentError(RoleError):
    __slots__ = ()


class RoleAlreadyAssignedError(RoleAssignmentError):
    __slots__ = ("_role", "_user_id")

    def __init__(self, role: SystemRole, user_id: UUID) -> None:
        self._role = role
        self._user_id = user_id
        super().__init__(f"Role {role.value!r} already assigned to user {user_id!r}")


class RoleNotAssignedError(RoleAssignmentError):
    __slots__ = ("_role", "_user_id")

    def __init__(self, role: SystemRole, user_id: UUID) -> None:
        self._role = role
        self._user_id = user_id
        super().__init__(f"Role {role.value!r} not assigned to user {user_id!r}")


class RoleHierarchyViolationError(RoleError):
    __slots__ = ("_action", "_target_role")

    def __init__(self, action: RoleAction, target_role: SystemRole) -> None:
        self._action = action
        self._target_role = target_role
        super().__init__(
            f"Cannot {action.value} role {target_role.value!r} with current privileges"
        )


class RoleSelfModificationError(RoleAssignmentError):
    __slots__ = ("_action", "_user_id")

    def __init__(self, action: RoleAction, user_id: UUID) -> None:
        self._action = action
        self._user_id = user_id
        super().__init__(f"User {user_id!r} cannot {action.value} roles for self")


class LastSuperAdminRemovalError(RoleAssignmentError):
    __slots__ = ("_user_id",)

    def __init__(self, user_id: UUID) -> None:
        self._user_id = user_id
        super().__init__(f"Cannot revoke last super_admin role from user {user_id!r}")
