from __future__ import annotations

from backend.application.common.dtos.rbac import AssignRoleToUserDTO, RoleResponseDTO
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.tools.handler_base import CommandHandler
from backend.application.common.tools.handler_transform import handler
from backend.domain.core.entities.base import TypeID


class AssignRoleToUserCommand(AssignRoleToUserDTO):
    role_id: TypeID
    user_id: TypeID


@handler(mode="write")
class AssignRoleToUserHandler(CommandHandler[AssignRoleToUserCommand, RoleResponseDTO]):
    uow: UnitOfWorkPort

    async def _execute(self, cmd: AssignRoleToUserCommand, /) -> RoleResponseDTO:
        async with self.uow:
            result = await self.uow.rbac.assign_role_to_user(
                user_id=cmd.user_id, role_id=cmd.role_id
            )
            await self.uow.commit()

        return result
