from __future__ import annotations

from collections.abc import Callable

from backend.application.common.exceptions.application import (
    AppError,
    AuthorizationError,
    ConflictError,
    RoleHierarchyViolationError,
)
from backend.domain.core.constants.rbac import RoleAction, SystemRole
from backend.domain.core.exceptions.rbac import (
    LastSuperAdminRemovalError,
    RoleAlreadyAssignedError,
    RoleNotAssignedError,
    RoleSelfModificationError,
)
from backend.domain.core.exceptions.rbac import (
    RoleHierarchyViolationError as DomainRoleHierarchyViolationError,
)


def map_role_input_error(
    raw_role: str, *, allow_unassigned: bool = False
) -> Callable[[Exception], AppError]:
    def mapper(exc: Exception) -> AppError:
        if isinstance(exc, ValueError):
            return ConflictError(f"Unknown role {raw_role!r}")
        if allow_unassigned and isinstance(exc, RoleNotAssignedError):
            return ConflictError(str(exc))
        raise exc

    return mapper


def map_role_change_error(
    *, action: RoleAction, target_role: SystemRole
) -> Callable[[Exception], AppError]:
    def mapper(exc: Exception) -> AppError:
        if isinstance(exc, DomainRoleHierarchyViolationError):
            return RoleHierarchyViolationError(
                action=action, target_role=target_role
            )
        if isinstance(exc, RoleSelfModificationError):
            return AuthorizationError(str(exc))
        if isinstance(
            exc,
            (
                RoleAlreadyAssignedError,
                RoleNotAssignedError,
                LastSuperAdminRemovalError,
            ),
        ):
            return ConflictError(str(exc))
        raise exc

    return mapper
