from __future__ import annotations

from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.domain.core.constants.rbac import RoleAction
from backend.domain.core.value_objects.access.permission_code import (
    PermissionCode,
)
from backend.domain.core.value_objects.access.role_code import RoleCode


@dataclass(frozen=True, slots=True)
class AppError(Exception):
    code: str
    message: str
    detail: str | None = None
    meta: dict[str, object] | None = None


class ConflictError(AppError):
    def __init__(
        self: ConflictError,
        message: str,
        *,
        detail: str | None = None,
        meta: dict[str, object] | None = None,
    ) -> None:
        super().__init__(
            code="conflict", message=message, detail=detail, meta=meta
        )


class UnknownRoleError(AppError):
    def __init__(self: UnknownRoleError) -> None:
        super().__init__(
            code="rbac.role_unknown",
            message="Role does not exist",
        )


class ResourceNotFoundError(AppError):
    def __init__(
        self: ResourceNotFoundError,
        resource: str,
        identifier: str,
        *,
        detail: str | None = None,
        meta: dict[str, object] | None = None,
    ) -> None:
        message = f"{resource} with identifier {identifier!r} not found"
        code = f"{resource}.not_found"
        super().__init__(code=code, message=message, detail=detail, meta=meta)


class PermissionDeniedError(AppError):
    def __init__(
        self: PermissionDeniedError,
        *,
        user_id: UUID,
        missing_permission: PermissionCode,
        detail: str | None = None,
    ) -> None:
        message = (
            f"User {user_id} lacks permission {missing_permission.value!r}"
        )
        super().__init__(
            code="auth.forbidden",
            message=message,
            detail=detail,
            meta={
                "user_id": str(user_id),
                "permission": missing_permission.value,
            },
        )


class RoleHierarchyViolationError(AppError):
    def __init__(
        self: RoleHierarchyViolationError,
        *,
        action: RoleAction,
        target_role: RoleCode,
        detail: str | None = None,
    ) -> None:
        message = f"Cannot {action.value} role {target_role.value!r} with current privileges"
        super().__init__(
            code="rbac.hierarchy_violation",
            message=message,
            detail=detail,
            meta={"action": action.value, "role": target_role.value},
        )


class UnauthenticatedError(AppError):
    def __init__(
        self: UnauthenticatedError, message: str = "Authentication required"
    ) -> None:
        super().__init__(code="auth.unauthenticated", message=message)


class AuthorizationError(AppError):
    def __init__(self: AuthorizationError, message: str = "Forbidden") -> None:
        super().__init__(code="auth.forbidden", message=message)
