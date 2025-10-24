from __future__ import annotations

from datetime import UTC

from fastapi_backend.application.common.dtos.users.users_dto import UserCreateDTO, UserResponseDTO
from fastapi_backend.application.common.services.handler_base import CommandHandler
from fastapi_backend.application.common.services.handler_transform import handler
from fastapi_backend.domain.core.value_objects.email import Email
from fastapi_backend.domain.core.value_objects.login import Login
from fastapi_backend.domain.core.value_objects.password import Password
from fastapi_backend.domain.core.value_objects.username import Username
from fastapi_backend.domain.ports.repositories.user_repository import UserRepositoryPort
from fastapi_backend.domain.ports.unit_of_work import UnitOfWorkPort
from fastapi_backend.domain.services.user_domain_service import UserDomainService


class CreateUserCommand(UserCreateDTO):
    login: str
    username: str
    password_hash: str


@handler(mode="write")
class CreateUserHandler(CommandHandler[CreateUserCommand, UserResponseDTO]):
    uow: UnitOfWorkPort
    user_repo: UserRepositoryPort
    user_service: UserDomainService

    async def _execute(self, cmd: CreateUserCommand, /) -> UserResponseDTO:
        async with self.uow:
            email = Email(cmd.email)
            login = Login(cmd.login)

            if await self.user_repo.exists_with_email(email):
                raise ValueError(f"Email {cmd.email!r} already exists")
            if await self.user_repo.exists_with_login(login):
                raise ValueError(f"Login {cmd.login!r} already exists")

            user = self.user_service.register_user(
                email=email,
                login=login,
                username=Username(cmd.username),
                password=Password(cmd.password_hash),
            )

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
