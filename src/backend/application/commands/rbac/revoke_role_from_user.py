from __future__ import annotations

from backend.application.common.dtos.rbac import RevokeRoleFromUserDTO, RoleResponseDTO
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.tools.handler_base import CommandHandler
from backend.application.common.tools.handler_transform import handler
from backend.domain.core.entities.base import TypeID


class RevokeRoleFromUserCommand(RevokeRoleFromUserDTO):
    role_id: TypeID
    user_id: TypeID


@handler(mode="write")
class RevokeRoleFromUserHandler(CommandHandler[RevokeRoleFromUserCommand, RoleResponseDTO]):
    uow: UnitOfWorkPort

    async def _execute(self, cmd: RevokeRoleFromUserCommand, /) -> RoleResponseDTO:
        async with self.uow:
            result = await self.uow.rbac.revoke_role_from_user(
                user_id=cmd.user_id, role_id=cmd.role_id
            )
            await self.uow.commit()

        return result
