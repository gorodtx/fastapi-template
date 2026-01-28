from __future__ import annotations

from collections.abc import Awaitable
from typing import Protocol

from uuid_utils.compat import UUID

from backend.application.common.exceptions.storage import StorageError
from backend.application.handlers.result import Result
from backend.domain.core.entities.user import User


class UsersAdapter(Protocol):
    def get_by_id(
        self: UsersAdapter, user_id: UUID, /
    ) -> Awaitable[Result[User, StorageError]]: ...

    def get_by_email(
        self: UsersAdapter, email: str, /
    ) -> Awaitable[Result[User, StorageError]]: ...

    def save(
        self: UsersAdapter, user: User, /
    ) -> Awaitable[Result[User, StorageError]]: ...

    def delete(
        self: UsersAdapter, user_id: UUID, /
    ) -> Awaitable[Result[bool, StorageError]]: ...
