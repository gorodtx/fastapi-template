from __future__ import annotations

from backend.application.common.dtos.users import UserResponseDTO, UserUpdateDTO
from backend.application.common.exceptions.application import ConflictError
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.tools.handler_base import CommandHandler
from backend.application.common.tools.handler_transform import handler
from backend.application.common.tools.password_validator import RawPasswordValidator
from backend.domain.core.entities.base import TypeID
from backend.domain.core.exceptions.base import DomainTypeError
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.password import Password
from backend.domain.ports.security.password_hasher import PasswordHasherPort


class UpdateUserCommand(UserUpdateDTO):
    user_id: TypeID
    email: str | None = None
    raw_password: str | None = None


@handler(mode="write")
class UpdateUserHandler(CommandHandler[UpdateUserCommand, UserResponseDTO]):
    uow: UnitOfWorkPort
    password_hasher: PasswordHasherPort

    async def _execute(self, cmd: UpdateUserCommand, /) -> UserResponseDTO:
        if cmd.email is None and cmd.raw_password is None:
            raise ConflictError("Nothing to update")

        email_vo: Email | None = None
        password_vo: Password | None = None

        if cmd.email is not None:
            try:
                email_vo = Email(cmd.email)
            except (ValueError, DomainTypeError) as e:
                raise ConflictError(f"Invalid email: {e}") from e

        if cmd.raw_password is not None:
            try:
                RawPasswordValidator.validate(cmd.raw_password)
            except ValueError as e:
                raise ConflictError(f"Invalid password: {e}") from e
            try:
                password_hash = await self.password_hasher.hash(cmd.raw_password)
            except RuntimeError as e:
                raise ConflictError(f"Password hashing failed: {e}") from e
            try:
                password_vo = Password(password_hash)
            except (ValueError, DomainTypeError) as e:
                raise ConflictError(f"Invalid password hash: {e}") from e

        async with self.uow:
            result = await self.uow.users.update(
                user_id=cmd.user_id,
                email=email_vo,
                password=password_vo,
            )
            await self.uow.commit()

        return result
