from __future__ import annotations

from backend.application.common.dtos.users import DeleteUserDTO, UserResponseDTO
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.storage import map_storage_error_to_app
from backend.application.common.interfaces.ports.persistence.gateway import PersistenceGateway
from backend.application.common.presenters.users import present_user_response
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import Result, ResultImpl
from backend.application.handlers.transform import handler


class DeleteUserCommand(DeleteUserDTO): ...


@handler(mode="write")
class DeleteUserHandler(CommandHandler[DeleteUserCommand, UserResponseDTO]):
    gateway: PersistenceGateway

    async def __call__(self, cmd: DeleteUserCommand, /) -> Result[UserResponseDTO, AppError]:
        async with self.gateway.manager.transaction():
            user_result = (await self.gateway.users.get_by_id(cmd.user_id)).map_err(
                map_storage_error_to_app()
            )
            if user_result.is_err():
                return ResultImpl.err_from(user_result)
            user = user_result.unwrap()

            delete_result = (await self.gateway.users.delete(cmd.user_id)).map_err(
                map_storage_error_to_app()
            )
            if delete_result.is_err():
                return ResultImpl.err_from(delete_result)

            return ResultImpl.ok(present_user_response(user))
