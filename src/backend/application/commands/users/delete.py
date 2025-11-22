from __future__ import annotations

from backend.application.common.dtos.users import DeleteUserDTO, UserResponseDTO
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.tools.handler_base import CommandHandler
from backend.application.common.tools.handler_transform import handler
from backend.domain.core.entities.base import TypeID


class DeleteUserCommand(DeleteUserDTO):
    user_id: TypeID


@handler(mode="write")
class DeleteUserHandler(CommandHandler[DeleteUserCommand, UserResponseDTO]):
    uow: UnitOfWorkPort

    async def _execute(self, cmd: DeleteUserCommand, /) -> UserResponseDTO:
        async with self.uow:
            result = await self.uow.users.delete(user_id=cmd.user_id)
            await self.uow.commit()

        return result
