from __future__ import annotations

from fastapi_backend.application.common.dtos.users.users_dto import (
    UserCreateDTO,
    UserResponseDTO,
)
from fastapi_backend.application.common.exceptions.application import ConflictError
from fastapi_backend.application.common.tools.handler_base import CommandHandler
from fastapi_backend.application.common.tools.handler_transform import handler
from fastapi_backend.application.common.tools.password_validator import RawPasswordValidator
from fastapi_backend.domain.core.exceptions.base import DomainError, DomainTypeError
from fastapi_backend.domain.core.exceptions.user import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from fastapi_backend.domain.core.value_objects.identity.email import Email
from fastapi_backend.domain.core.value_objects.identity.login import Login
from fastapi_backend.domain.core.value_objects.identity.username import Username
from fastapi_backend.domain.core.value_objects.password import Password
from fastapi_backend.domain.ports.repositories.user_repository import UserRepositoryPort
from fastapi_backend.domain.ports.security.password_hasher import PasswordHasherPort
from fastapi_backend.domain.ports.unit_of_work import UnitOfWorkPort
from fastapi_backend.domain.services.user_domain_service import UserDomainService


class CreateUserCommand(UserCreateDTO):
    email: str
    login: str
    username: str
    raw_password: str


@handler(mode="write")
class CreateUserHandler(CommandHandler[CreateUserCommand, UserResponseDTO]):
    uow: UnitOfWorkPort
    user_repo: UserRepositoryPort
    user_service: UserDomainService
    password_hasher: PasswordHasherPort

    async def _execute(self, cmd: CreateUserCommand, /) -> UserResponseDTO:
        async with self.uow:
            try:
                RawPasswordValidator.validate(cmd.raw_password)
            except ValueError as e:
                raise ConflictError(f"Invalid password: {e}") from e

            try:
                password_hash = await self.password_hasher.hash(cmd.raw_password)
            except RuntimeError as e:
                raise ConflictError(f"Password hashing failed: {e}") from e

            try:
                email = Email(cmd.email)
                login = Login(cmd.login)
                username = Username(cmd.username)
                password = Password(password_hash)
            except (ValueError, DomainTypeError) as e:
                raise ConflictError(f"Invalid input: {e}") from e

            if await self.user_repo.exists_with_email(email):
                raise ConflictError(f"Email {cmd.email!r} already registered")
            if await self.user_repo.exists_with_login(login):
                raise ConflictError(f"Login {cmd.login!r} already taken")
            if await self.user_repo.exists_with_username(username):
                raise ConflictError(f"Username {cmd.username!r} already taken")

            try:
                user = await self.user_service.register_user(
                    email=email,
                    login=login,
                    username=username,
                    password=password,
                )
            except (EmailAlreadyExistsError, UsernameAlreadyExistsError) as e:
                raise ConflictError(str(e)) from e
            except DomainError as e:
                raise ConflictError(f"Cannot create user: {e}") from e

            await self.user_repo.save(user)
            await self.uow.commit()

        return UserResponseDTO(
            id=user.id,
            email=user.email.value,
            is_active=True,
        )
