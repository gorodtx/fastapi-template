from __future__ import annotations

from typing import Protocol

from fastapi_backend.domain.core.value_objects.identity.email import Email
from fastapi_backend.domain.core.value_objects.identity.login import Login
from fastapi_backend.domain.core.value_objects.identity.username import Username
from src.fastapi_backend.domain.core.entities.base import TypeID
from src.fastapi_backend.domain.core.entities.user import User


class UserRepositoryPort(Protocol):
    async def find_by_id(self, user_id: TypeID) -> User | None: ...

    async def find_by_email(self, email: Email) -> User | None: ...

    async def find_by_login(self, login: Login) -> User | None: ...

    async def exists_with_email(self, email: Email, exclude_id: TypeID | None = None) -> bool: ...

    async def exists_with_login(self, login: Login, exclude_id: TypeID | None = None) -> bool: ...

    async def exists_with_username(
        self, username: Username, exclude_id: TypeID | None = None
    ) -> bool: ...

    async def save(self, user: User) -> None: ...

    async def delete(self, user: User) -> None: ...

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]: ...
