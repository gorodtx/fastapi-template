from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.common.dtos.users import UserResponseDTO
from backend.domain.core.entities.base import TypeID
from backend.domain.core.entities.user import User
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.password import Password
from backend.infrastructure.persistence.sqlalchemy.models import UserModel


class UsersRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: User) -> UserResponseDTO:
        model = UserModel(
            id=user.id,
            email=user.email.value,
            login=user.login.value,
            username=user.username.value,
            password_hash=user.password.value,
            is_active=True,
        )
        self._session.add(model)
        await self._session.flush()

        return UserResponseDTO.from_(model)

    async def update(
        self,
        *,
        user_id: TypeID,
        email: Email | None,
        password: Password | None,
    ) -> UserResponseDTO:
        model = await self._session.get(UserModel, user_id)
        if model is None:
            raise LookupError(f"User {user_id!r} not found")

        if email is not None:
            model.email = email.value
        if password is not None:
            model.password_hash = password.value

        await self._session.flush()

        return UserResponseDTO.from_(model)

    async def delete(self, *, user_id: TypeID) -> UserResponseDTO:
        model = await self._session.get(UserModel, user_id)
        if model is None:
            raise LookupError(f"User {user_id!r} not found")

        dto = UserResponseDTO.from_(model)

        await self._session.delete(model)
        await self._session.flush()

        return dto

    async def get_one(self, *, user_id: TypeID) -> UserResponseDTO:
        model = await self._session.get(UserModel, user_id)
        if model is None:
            raise LookupError(f"User {user_id!r} not found")

        return UserResponseDTO.from_(model)
