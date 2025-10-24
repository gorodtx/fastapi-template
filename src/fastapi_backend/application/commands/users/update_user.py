from __future__ import annotations

from datetime import UTC

from fastapi_backend.application.common.dtos.users.users_dto import UserResponseDTO, UserUpdateDTO
from fastapi_backend.application.common.services.handler_base import CommandHandler
from fastapi_backend.application.common.services.handler_transform import handler
from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.core.value_objects.email import Email
from fastapi_backend.domain.core.value_objects.password import Password
from fastapi_backend.domain.ports.repositories.user_repository import UserRepositoryPort
from fastapi_backend.domain.ports.unit_of_work import UnitOfWorkPort
from fastapi_backend.domain.services.user_domain_service import UserDomainService


class UpdateUserCommand(UserUpdateDTO):
    user_id: str


@handler(mode="write")
class UpdateUserHandler(CommandHandler[UpdateUserCommand, UserResponseDTO]):
    uow: UnitOfWorkPort
    user_repo: UserRepositoryPort
    user_service: UserDomainService

    async def _execute(self, cmd: UpdateUserCommand, /) -> UserResponseDTO:
        async with self.uow:
            uid = TypeID(cmd.user_id)
            user = await self.user_repo.find_by_id(uid)
            if not user:
                raise LookupError(f"User {cmd.user_id!r} not found")

            if cmd.email:
                new_email = Email(cmd.email)
                if await self.user_repo.exists_with_email(new_email, exclude_id=uid):
                    raise ValueError(f"Email {cmd.email!r} already exists")
                self.user_service.change_user_email(user, new_email)

            if cmd.password:
                self.user_service.change_user_password(user, Password(cmd.password))

            await self.user_repo.save(user)
            await self.uow.commit()

        from datetime import datetime

        return UserResponseDTO(
            id=user.id,
            email=user.email.value,
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
