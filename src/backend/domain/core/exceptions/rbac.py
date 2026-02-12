from __future__ import annotations

from uuid_utils.compat import UUID

from backend.domain.core.constants.rbac import RoleAction
from backend.domain.core.exceptions.base import DomainError
from backend.domain.core.types.rbac import RoleCode


class RoleError(DomainError):
    """Base role domain error."""

    __slots__: tuple[str, ...] = ()


class RoleAssignmentError(RoleError):
    __slots__: tuple[str, ...] = ()


class RoleAlreadyAssignedError(RoleAssignmentError):
    __slots__: tuple[str, ...] = ("_role", "_user_id")

    def __init__(
        self: RoleAlreadyAssignedError, role: RoleCode, user_id: UUID
    ) -> None:
        self._role = role
        self._user_id = user_id
        super().__init__(f"Role {role!r} already assigned to user {user_id!r}")


class RoleNotAssignedError(RoleAssignmentError):
    __slots__: tuple[str, ...] = ("_role", "_user_id")

    def __init__(
        self: RoleNotAssignedError, role: RoleCode, user_id: UUID
    ) -> None:
        self._role = role
        self._user_id = user_id
        super().__init__(f"Role {role!r} not assigned to user {user_id!r}")


class RoleHierarchyViolationError(RoleError):
    __slots__: tuple[str, ...] = ("_action", "_target_role")

    def __init__(
        self: RoleHierarchyViolationError,
        action: RoleAction,
        target_role: RoleCode,
    ) -> None:
        self._action = action
        self._target_role = target_role
        super().__init__(
            f"Cannot {action.value} role {target_role!r} with current privileges"
        )


class RoleSelfModificationError(RoleAssignmentError):
    __slots__: tuple[str, ...] = ("_action", "_user_id")

    def __init__(
        self: RoleSelfModificationError, action: RoleAction, user_id: UUID
    ) -> None:
        self._action = action
        self._user_id = user_id
        super().__init__(
            f"User {user_id!r} cannot {action.value} roles for self"
        )


class LastSuperAdminRemovalError(RoleAssignmentError):
    __slots__: tuple[str, ...] = ("_user_id",)

    def __init__(self: LastSuperAdminRemovalError, user_id: UUID) -> None:
        self._user_id = user_id
        super().__init__(
            f"Cannot revoke last super_admin role from user {user_id!r}"
        )
