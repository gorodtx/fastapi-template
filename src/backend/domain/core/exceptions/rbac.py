from __future__ import annotations

from backend.domain.core.entities.base import TypeID
from backend.domain.core.exceptions.base import DomainError
from backend.domain.core.value_objects.access.permission_code import PermissionCode
from backend.domain.core.value_objects.identity.role_name import RoleName


class RoleError(DomainError):
    """Base role domain error."""

    __slots__ = ()


class RoleAlreadyExistsError(RoleError):
    __slots__ = ("_role_name",)

    def __init__(self, role_name: RoleName) -> None:
        self._role_name = role_name
        super().__init__(f"Role {role_name.value!r} already exists")


class RoleNotFoundError(RoleError):
    __slots__ = ("_role_id",)

    def __init__(self, role_id: TypeID) -> None:
        self._role_id = role_id
        super().__init__(f"Role {role_id!r} not found")


class PermissionError(RoleError):
    __slots__ = ()


class PermissionAlreadyGrantedError(PermissionError):
    __slots__ = ("_permission",)

    def __init__(self, permission: PermissionCode) -> None:
        self._permission = permission
        super().__init__(f"Permission {permission.value!r} already granted")


class PermissionNotGrantedError(PermissionError):
    __slots__ = ("_permission",)

    def __init__(self, permission: PermissionCode) -> None:
        self._permission = permission
        super().__init__(f"Permission {permission.value!r} not granted")


class RoleAssignmentError(RoleError):
    __slots__ = ()


class RoleAlreadyAssignedError(RoleAssignmentError):
    __slots__ = ("_role_id", "_user_id")

    def __init__(self, role_id: TypeID, user_id: TypeID) -> None:
        self._role_id = role_id
        self._user_id = user_id
        super().__init__(f"Role {role_id!r} already assigned to user {user_id!r}")


class RoleNotAssignedError(RoleAssignmentError):
    __slots__ = ("_role_id", "_user_id")

    def __init__(self, role_id: TypeID, user_id: TypeID) -> None:
        self._role_id = role_id
        self._user_id = user_id
        super().__init__(f"Role {role_id!r} not assigned to user {user_id!r}")
