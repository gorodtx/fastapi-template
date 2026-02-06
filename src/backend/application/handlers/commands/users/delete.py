from __future__ import annotations

from backend.application.common.dtos.auth import SuccessDTO
from backend.application.common.dtos.users import (
    DeleteUserDTO,
)
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.tools.auth_cache import AuthCacheInvalidator
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import Result, ResultImpl
from backend.application.handlers.transform import handler


class DeleteUserCommand(DeleteUserDTO): ...


@handler(mode="write")
class DeleteUserHandler(CommandHandler[DeleteUserCommand, SuccessDTO]):
    gateway: PersistenceGateway
    cache_invalidator: AuthCacheInvalidator

    async def __call__(
        self: DeleteUserHandler, cmd: DeleteUserCommand, /
    ) -> Result[SuccessDTO, AppError]:
        async with self.gateway.manager.transaction():
            user_result = (
                await self.gateway.users.get_by_id(
                    cmd.user_id,
                    include_roles=False,
                )
            ).map_err(map_storage_error_to_app())
            if user_result.is_err():
                return ResultImpl.err_from(user_result)
            user_result.unwrap()

            delete_result = (
                await self.gateway.users.delete(cmd.user_id)
            ).map_err(map_storage_error_to_app())
            if delete_result.is_err():
                return ResultImpl.err_from(delete_result)

            response: Result[SuccessDTO, AppError] = ResultImpl.ok(
                SuccessDTO(),
                AppError,
            )

        await self.cache_invalidator.invalidate_user(cmd.user_id)
        return response
