from __future__ import annotations

from fastapi_backend.application.common.dtos.users.users_dto import (
    UserResponseDTO,
    UserUpdateDTO,
)
from fastapi_backend.application.common.exceptions.application import (
    ConflictError,
    ResourceNotFoundError,
)
from fastapi_backend.application.common.tools.handler_base import CommandHandler
from fastapi_backend.application.common.tools.handler_transform import handler
from fastapi_backend.application.common.tools.password_validator import RawPasswordValidator
from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.core.exceptions.base import DomainError, DomainTypeError
from fastapi_backend.domain.core.value_objects.identity.email import Email
from fastapi_backend.domain.core.value_objects.password import Password
from fastapi_backend.domain.ports.repositories.user_repository import UserRepositoryPort
from fastapi_backend.domain.ports.security.password_hasher import PasswordHasherPort
from fastapi_backend.domain.ports.unit_of_work import UnitOfWorkPort
from fastapi_backend.domain.services.user_domain_service import UserDomainService


class UpdateUserCommand(UserUpdateDTO):
    user_id: str
    email: str | None = None
    raw_password: str | None = None


@handler(mode="write")
class UpdateUserHandler(CommandHandler[UpdateUserCommand, UserResponseDTO]):
    uow: UnitOfWorkPort
    user_repo: UserRepositoryPort
    user_service: UserDomainService
    password_hasher: PasswordHasherPort

    async def _execute(self, cmd: UpdateUserCommand, /) -> UserResponseDTO:
        async with self.uow:
            uid = TypeID(cmd.user_id)
            user = await self.user_repo.find_by_id(uid)

            if not user:
                raise ResourceNotFoundError("User", cmd.user_id)

            if cmd.email:
                try:
                    new_email = Email(cmd.email)
                except (ValueError, DomainTypeError) as e:
                    raise ConflictError(f"Invalid email: {e}") from e

                if await self.user_repo.exists_with_email(new_email, exclude_id=uid):
                    raise ConflictError(f"Email {cmd.email!r} already registered")

                try:
                    await self.user_service.change_user_email(user, new_email)
                except DomainError as e:
                    raise ConflictError(f"Cannot change email: {e}") from e

            if cmd.raw_password:
                try:
                    RawPasswordValidator.validate(cmd.raw_password)
                except ValueError as e:
                    raise ConflictError(f"Invalid password: {e}") from e

                try:
                    password_hash = await self.password_hasher.hash(cmd.raw_password)
                except RuntimeError as e:
                    raise ConflictError(f"Password hashing failed: {e}") from e

                try:
                    new_password = Password(password_hash)
                except (ValueError, DomainTypeError) as e:
                    raise ConflictError(f"Invalid password hash: {e}") from e

                try:
                    await self.user_service.change_user_password(user, new_password)
                except DomainError as e:
                    raise ConflictError(f"Cannot change password: {e}") from e

            await self.user_repo.save(user)
            await self.uow.commit()

        return UserResponseDTO(
            id=user.id,
            email=user.email.value,
            is_active=True,
        )
