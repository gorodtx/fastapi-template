from __future__ import annotations

from collections.abc import Awaitable
from typing import Protocol

from uuid_utils.compat import UUID

from backend.application.common.exceptions.storage import StorageError
from backend.application.handlers.result import Result
from backend.domain.core.entities.user import User


class UsersAdapter(Protocol):
    def get_by_id(self, user_id: UUID, /) -> Awaitable[Result[User, StorageError]]: ...

    def save(self, user: User, /) -> Awaitable[Result[User, StorageError]]: ...

    def delete(self, user_id: UUID, /) -> Awaitable[Result[bool, StorageError]]: ...
