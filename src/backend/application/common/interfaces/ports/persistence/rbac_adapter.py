from __future__ import annotations

from collections.abc import Awaitable
from typing import Protocol

from uuid_utils.compat import UUID

from backend.application.common.exceptions.storage import StorageError
from backend.application.handlers.result import Result
from backend.domain.core.constants.rbac import SystemRole


class RbacAdapter(Protocol):
    def get_user_roles(
        self: RbacAdapter, user_id: UUID, /
    ) -> Awaitable[Result[set[SystemRole], StorageError]]: ...

    def replace_user_roles(
        self: RbacAdapter, user_id: UUID, roles: set[SystemRole], /
    ) -> Awaitable[Result[None, StorageError]]: ...

    def list_user_ids_by_role(
        self: RbacAdapter, role: SystemRole, /
    ) -> Awaitable[Result[list[UUID], StorageError]]: ...
