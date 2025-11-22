from __future__ import annotations

from backend.application.common.dtos.rbac import GrantPermissionDTO, RoleResponseDTO
from backend.application.common.exceptions.application import ConflictError
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.tools.handler_base import CommandHandler
from backend.application.common.tools.handler_transform import handler
from backend.domain.core.entities.base import TypeID
from backend.domain.core.exceptions.base import DomainTypeError
from backend.domain.core.value_objects.access.permission_code import PermissionCode


class GrantPermissionCommand(GrantPermissionDTO):
    role_id: TypeID
    permission: str


@handler(mode="write")
class GrantPermissionHandler(CommandHandler[GrantPermissionCommand, RoleResponseDTO]):
    uow: UnitOfWorkPort

    async def _execute(self, cmd: GrantPermissionCommand, /) -> RoleResponseDTO:
        try:
            perm_vo = PermissionCode(cmd.permission)
        except (ValueError, DomainTypeError) as e:
            raise ConflictError(f"Invalid permission: {e}") from e

        async with self.uow:
            result = await self.uow.rbac.grant_permission(role_id=cmd.role_id, perm=perm_vo)
            await self.uow.commit()

        return result
