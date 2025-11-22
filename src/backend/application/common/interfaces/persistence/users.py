from __future__ import annotations

from typing import Protocol

from backend.application.common.dtos.users import UserResponseDTO
from backend.domain.core.entities.base import TypeID
from backend.domain.core.entities.user import User
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.password import Password


class UsersPort(Protocol):
    async def create(self, user: User) -> UserResponseDTO: ...

    async def update(
        self,
        *,
        user_id: TypeID,
        email: Email | None,
        password: Password | None,
    ) -> UserResponseDTO: ...

    async def delete(self, *, user_id: TypeID) -> UserResponseDTO: ...

    async def get_one(self, *, user_id: TypeID) -> UserResponseDTO: ...
