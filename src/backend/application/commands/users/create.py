from __future__ import annotations

import uuid_utils.compat as uuid

from backend.application.common.dtos.users import UserCreateDTO, UserResponseDTO
from backend.application.common.exceptions.application import ConflictError
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.tools.handler_base import CommandHandler
from backend.application.common.tools.handler_transform import handler
from backend.application.common.tools.password_validator import RawPasswordValidator
from backend.domain.core.entities.user import User
from backend.domain.core.exceptions.base import DomainError, DomainTypeError
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.domain.core.value_objects.password import Password
from backend.domain.ports.security.password_hasher import PasswordHasherPort


class CreateUserCommand(UserCreateDTO):
    email: str
    login: str
    username: str
    raw_password: str


@handler(mode="write")
class CreateUserHandler(CommandHandler[CreateUserCommand, UserResponseDTO]):
    uow: UnitOfWorkPort
    password_hasher: PasswordHasherPort

    async def _execute(self, cmd: CreateUserCommand, /) -> UserResponseDTO:
        try:
            RawPasswordValidator.validate(cmd.raw_password)
        except ValueError as e:
            raise ConflictError(f"Invalid password: {e}") from e

        try:
            password_hash = await self.password_hasher.hash(cmd.raw_password)
        except RuntimeError as e:
            raise ConflictError(f"Password hashing failed: {e}") from e

        try:
            user = User.register(
                id=uuid.uuid7(),
                email=Email(cmd.email),
                login=Login(cmd.login),
                username=Username(cmd.username),
                password=Password(password_hash),
            )
        except (ValueError, DomainTypeError, DomainError) as e:
            raise ConflictError(f"Invalid input: {e}") from e

        async with self.uow:
            result = await self.uow.users.create(user)
            await self.uow.commit()

        return result
