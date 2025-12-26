from __future__ import annotations

from typing import Protocol

from backend.domain.core.entities.base import TypeID
from backend.domain.core.entities.user import User
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.password import Password


class UsersPort(Protocol):
    async def create(self, user: User) -> User: ...

    async def update(
        self,
        *,
        user_id: TypeID,
        email: Email | None,
        password: Password | None,
    ) -> User: ...

    async def delete(self, *, user_id: TypeID) -> User: ...

    async def get_one(self, *, user_id: TypeID) -> User: ...
