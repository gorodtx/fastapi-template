from __future__ import annotations

from collections.abc import Callable

from backend.application.common.exceptions.application import (
    AppError,
    AuthorizationError,
    ConflictError,
    RoleHierarchyViolationError,
    UnknownRoleError,
)
from backend.domain.core.constants.rbac import RoleAction
from backend.domain.core.exceptions.rbac import (
    LastSuperAdminRemovalError,
    RoleAlreadyAssignedError,
    RoleNotAssignedError,
    RoleSelfModificationError,
)
from backend.domain.core.exceptions.rbac import (
    RoleHierarchyViolationError as DomainRoleHierarchyViolationError,
)
from backend.domain.core.value_objects.access.role_code import RoleCode


def map_role_input_error(
    _raw_role: str, *, allow_unassigned: bool = False
) -> Callable[[Exception], AppError]:
    def mapper(exc: Exception) -> AppError:
        if isinstance(exc, ValueError):
            return UnknownRoleError()
        if allow_unassigned and isinstance(exc, RoleNotAssignedError):
            return ConflictError("Role not assigned")
        raise exc

    return mapper


def map_role_change_error(
    *, action: RoleAction, target_role: RoleCode
) -> Callable[[Exception], AppError]:
    def mapper(exc: Exception) -> AppError:
        if isinstance(exc, DomainRoleHierarchyViolationError):
            return RoleHierarchyViolationError(
                action=action, target_role=target_role
            )
        if isinstance(exc, RoleSelfModificationError):
            return AuthorizationError("Cannot modify own roles")
        if isinstance(
            exc,
            (
                RoleAlreadyAssignedError,
                RoleNotAssignedError,
            ),
        ):
            message = (
                "Role already assigned"
                if isinstance(exc, RoleAlreadyAssignedError)
                else "Role not assigned"
            )
            return ConflictError(message)
        if isinstance(exc, LastSuperAdminRemovalError):
            return ConflictError("Cannot remove last super_admin role")
        raise exc

    return mapper
