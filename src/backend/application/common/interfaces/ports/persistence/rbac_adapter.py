from __future__ import annotations

from collections.abc import Awaitable
from typing import Protocol

from uuid_utils.compat import UUID

from backend.application.common.exceptions.storage import StorageError
from backend.application.handlers.result import Result
from backend.domain.core.value_objects.access.permission_code import (
    PermissionCode,
)
from backend.domain.core.value_objects.access.role_code import RoleCode


class RbacAdapter(Protocol):
    def get_user_roles(
        self: RbacAdapter, user_id: UUID, /
    ) -> Awaitable[Result[set[RoleCode], StorageError]]: ...

    def get_user_permission_codes(
        self: RbacAdapter, user_id: UUID, /
    ) -> Awaitable[Result[set[PermissionCode], StorageError]]: ...

    def replace_user_roles(
        self: RbacAdapter, user_id: UUID, roles: set[RoleCode], /
    ) -> Awaitable[Result[None, StorageError]]: ...

    def list_user_ids_by_role(
        self: RbacAdapter, role: RoleCode, /
    ) -> Awaitable[Result[list[UUID], StorageError]]: ...
