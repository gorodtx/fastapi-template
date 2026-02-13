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
from backend.application.common.tools.tx_result import run_in_tx
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import Result
from backend.application.handlers.transform import handler


class DeleteUserCommand(DeleteUserDTO): ...


@handler(mode="write")
class DeleteUserHandler(CommandHandler[DeleteUserCommand, SuccessDTO]):
    gateway: PersistenceGateway

    async def __call__(
        self: DeleteUserHandler, cmd: DeleteUserCommand, /
    ) -> Result[SuccessDTO, AppError]:
        async def action() -> SuccessDTO:
            (
                await self.gateway.users.get_by_id(
                    cmd.user_id,
                    include_roles=False,
                )
            ).map_err(map_storage_error_to_app()).unwrap()

            (await self.gateway.users.delete(cmd.user_id)).map_err(
                map_storage_error_to_app()
            ).unwrap()

            return SuccessDTO()

        return await run_in_tx(
            manager=self.gateway.manager,
            action=action,
            value_type=SuccessDTO,
        )
