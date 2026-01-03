from __future__ import annotations

import uuid_utils.compat as uuid

from backend.application.common.dtos.users import UserCreateDTO, UserResponseDTO
from backend.application.common.exceptions.application import ConflictError
from backend.application.common.exceptions.db import ConstraintViolationError
from backend.application.common.exceptions.infra_mapper import map_infra_error_to_application
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.services.authorization import AuthorizationService
from backend.application.common.tools.password_validator import RawPasswordValidator
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.mappers import UserMapper
from backend.application.handlers.transform import handler
from backend.domain.core.constants.permission_codes import USERS_CREATE
from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.base import TypeID
from backend.domain.core.entities.user import User
from backend.domain.core.exceptions.base import DomainError, DomainTypeError
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.domain.core.value_objects.password import Password
from backend.domain.ports.security.password_hasher import PasswordHasherPort


class CreateUserCommand(UserCreateDTO):
    actor_id: TypeID
    email: str
    login: str
    username: str
    raw_password: str


@handler(mode="write")
class CreateUserHandler(CommandHandler[CreateUserCommand, UserResponseDTO]):
    uow: UnitOfWorkPort
    password_hasher: PasswordHasherPort
    authorization_service: AuthorizationService

    async def _execute(self, cmd: CreateUserCommand, /) -> UserResponseDTO:
        async with self.uow:
            await self.authorization_service.require_permission(
                user_id=cmd.actor_id,
                permission=USERS_CREATE,
                rbac=self.uow.rbac,
            )
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
            user.assign_role(SystemRole.USER)
            await self.uow.users.add(user)
            try:
                await self.uow.flush()
                await self.uow.users.assign_role_to_user(
                    user_id=user.id,
                    role=SystemRole.USER,
                )
                await self.uow.commit()
            except ConstraintViolationError as exc:
                raise map_infra_error_to_application(exc) from exc

        return UserMapper.to_dto(user)
