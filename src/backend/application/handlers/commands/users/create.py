from __future__ import annotations

from collections.abc import Awaitable

import uuid_utils.compat as uuid

from backend.application.common.dtos.users import (
    UserCreateDTO,
    UserResponseDTO,
)
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.exceptions.error_mappers.users import (
    map_user_input_error,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.presenters.users import present_user_response
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import (
    Result,
    ResultImpl,
    capture,
    capture_async,
)
from backend.application.handlers.transform import handler
from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.user import User
from backend.domain.core.factories.users import UserFactory
from backend.domain.ports.security.password_hasher import PasswordHasherPort


class CreateUserCommand(UserCreateDTO): ...


@handler(mode="write")
class CreateUserHandler(CommandHandler[CreateUserCommand, UserResponseDTO]):
    gateway: PersistenceGateway
    password_hasher: PasswordHasherPort

    async def __call__(
        self: CreateUserHandler, cmd: CreateUserCommand, /
    ) -> Result[UserResponseDTO, AppError]:
        def hash_password() -> Awaitable[str]:
            return self.password_hasher.hash(cmd.raw_password)

        hashed_result = await capture_async(
            hash_password, map_user_input_error()
        )
        if hashed_result.is_err():
            return ResultImpl.err_from(hashed_result)
        hashed = hashed_result.unwrap()

        def register_user() -> User:
            return UserFactory.register(
                id=uuid.uuid7(),
                email=cmd.email,
                login=cmd.login,
                username=cmd.username,
                password_hash=hashed,
            )

        user_result = capture(register_user, map_user_input_error())
        if user_result.is_err():
            return ResultImpl.err_from(user_result)
        user = user_result.unwrap()

        async with self.gateway.manager.transaction():
            user.assign_role(SystemRole.USER)

            save_result = (
                await self.gateway.users.save(user, include_roles=False)
            ).map_err(map_storage_error_to_app())
            if save_result.is_err():
                return ResultImpl.err_from(save_result)

            role_result = (
                await self.gateway.rbac.replace_user_roles(
                    user.id, {SystemRole.USER}
                )
            ).map_err(map_storage_error_to_app())
            if role_result.is_err():
                return ResultImpl.err_from(role_result)

            return save_result.map(present_user_response)
