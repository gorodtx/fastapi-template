from __future__ import annotations

from backend.application.common.dtos.users import UserResponseDTO, UserUpdateDTO
from backend.application.common.exceptions.application import ConflictError
from backend.application.common.exceptions.db import ConstraintViolationError
from backend.application.common.exceptions.infra_mapper import map_infra_error_to_application
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.services.authorization import AuthorizationService
from backend.application.common.tools.password_validator import RawPasswordValidator
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.mappers import UserMapper
from backend.application.handlers.transform import handler
from backend.domain.core.constants.permission_codes import USERS_UPDATE
from backend.domain.core.entities.base import TypeID
from backend.domain.core.exceptions.base import DomainTypeError
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.password import Password
from backend.domain.ports.security.password_hasher import PasswordHasherPort


class UpdateUserCommand(UserUpdateDTO):
    actor_id: TypeID
    user_id: TypeID
    email: str | None = None
    raw_password: str | None = None


@handler(mode="write")
class UpdateUserHandler(CommandHandler[UpdateUserCommand, UserResponseDTO]):
    uow: UnitOfWorkPort
    password_hasher: PasswordHasherPort
    authorization_service: AuthorizationService

    async def _execute(self, cmd: UpdateUserCommand, /) -> UserResponseDTO:
        async with self.uow:
            await self.authorization_service.require_permission(
                user_id=cmd.actor_id,
                permission=USERS_UPDATE,
                rbac=self.uow.rbac,
            )
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
            user = await self.uow.users.get(cmd.user_id)
            if user is None:
                raise LookupError(f"User {cmd.user_id!r} not found")
            if email_vo is not None:
                user.change_email(email_vo)
            if password_vo is not None:
                user.change_password(password_vo)
            try:
                await self.uow.commit()
            except ConstraintViolationError as exc:
                raise map_infra_error_to_application(exc) from exc

        return UserMapper.to_dto(user)
