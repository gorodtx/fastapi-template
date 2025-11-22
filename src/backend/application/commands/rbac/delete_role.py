from __future__ import annotations

from backend.application.common.dtos.rbac import RoleDeleteDTO, RoleResponseDTO
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.tools.handler_base import CommandHandler
from backend.application.common.tools.handler_transform import handler
from backend.domain.core.entities.base import TypeID


class DeleteRoleCommand(RoleDeleteDTO):
    role_id: TypeID


@handler(mode="write")
class DeleteRoleHandler(CommandHandler[DeleteRoleCommand, RoleResponseDTO]):
    uow: UnitOfWorkPort

    async def _execute(self, cmd: DeleteRoleCommand, /) -> RoleResponseDTO:
        async with self.uow:
            result = await self.uow.rbac.delete_role(role_id=cmd.role_id)
            await self.uow.commit()

        return result
