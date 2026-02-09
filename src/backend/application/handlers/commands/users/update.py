from __future__ import annotations

from collections.abc import Awaitable

from backend.application.common.dtos.users import (
    UserResponseDTO,
    UserUpdateDTO,
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
from backend.application.common.tools.auth_cache import AuthCacheInvalidator
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import (
    Result,
    ResultImpl,
    capture,
    capture_async,
)
from backend.application.handlers.transform import handler
from backend.domain.core.factories.users import UserFactory
from backend.domain.ports.security.password_hasher import PasswordHasherPort


class UpdateUserCommand(UserUpdateDTO): ...


@handler(mode="write")
class UpdateUserHandler(CommandHandler[UpdateUserCommand, UserResponseDTO]):
    gateway: PersistenceGateway
    password_hasher: PasswordHasherPort
    cache_invalidator: AuthCacheInvalidator

    async def __call__(
        self: UpdateUserHandler, cmd: UpdateUserCommand, /
    ) -> Result[UserResponseDTO, AppError]:
        async with self.gateway.manager.transaction():
            user_result = (
                await self.gateway.users.get_by_id(
                    cmd.user_id,
                    include_roles=False,
                )
            ).map_err(map_storage_error_to_app())
            if user_result.is_err():
                return ResultImpl.err_from(user_result)

            user = user_result.unwrap()

            if cmd.email is not None:

                def apply_email() -> None:
                    UserFactory.patch(user, email=cmd.email)

                change_result = capture(apply_email, map_user_input_error())
                if change_result.is_err():
                    return ResultImpl.err_from(change_result)

            if cmd.raw_password is not None:
                raw_password = cmd.raw_password

                def hash_password() -> Awaitable[str]:
                    return self.password_hasher.hash(raw_password)

                hashed_result = await capture_async(
                    hash_password, map_user_input_error()
                )
                if hashed_result.is_err():
                    return ResultImpl.err_from(hashed_result)
                hashed = hashed_result.unwrap()

                def apply_password() -> None:
                    UserFactory.patch(user, password_hash=hashed)

                change_result = capture(apply_password, map_user_input_error())
                if change_result.is_err():
                    return ResultImpl.err_from(change_result)

            save_result = (
                await self.gateway.users.save(user, include_roles=False)
            ).map_err(map_storage_error_to_app())
            if save_result.is_err():
                return ResultImpl.err_from(save_result)

            response = save_result.map(present_user_response)

        await self.cache_invalidator.invalidate_user(cmd.user_id)
        return response
