from __future__ import annotations

from backend.domain.core.constants.rbac import RoleAction, SystemRole
from backend.domain.core.entities.base import TypeID
from backend.domain.core.value_objects.access.permission_code import PermissionCode


class ApplicationError(Exception): ...


class ResourceNotFoundError(ApplicationError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"{resource} with identifier {identifier!r} not found")


class ConflictError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class PermissionDeniedError(ApplicationError):
    def __init__(self, *, user_id: TypeID, missing_permission: PermissionCode) -> None:
        self.user_id = user_id
        self.missing_permission = missing_permission
        super().__init__(f"User {user_id} lacks permission {missing_permission.value!r}")


class RoleHierarchyViolationError(ApplicationError):
    def __init__(self, *, action: RoleAction, target_role: SystemRole) -> None:
        self.action = action
        self.target_role = target_role
        super().__init__(
            f"Cannot {action.value} role {target_role.value!r} with current privileges"
        )
