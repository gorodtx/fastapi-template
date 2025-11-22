from __future__ import annotations

from backend.application.common.dtos.rbac import (
    RoleResponseDTO,
    RoleUpdateDTO,
)
from backend.application.common.exceptions.application import ConflictError
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.tools.handler_base import CommandHandler
from backend.application.common.tools.handler_transform import handler
from backend.domain.core.entities.base import TypeID
from backend.domain.core.exceptions.base import DomainTypeError
from backend.domain.core.value_objects.identity.role_name import RoleName


class UpdateRoleCommand(RoleUpdateDTO):
    role_id: TypeID
    name: str | None = None
    description: str | None = None


@handler(mode="write")
class UpdateRoleHandler(CommandHandler[UpdateRoleCommand, RoleResponseDTO]):
    uow: UnitOfWorkPort

    async def _execute(self, cmd: UpdateRoleCommand, /) -> RoleResponseDTO:
        if cmd.name is None:
            raise ConflictError("Nothing to update")

        try:
            name_vo = RoleName(cmd.name)
        except (ValueError, DomainTypeError) as e:
            raise ConflictError(f"Invalid role name: {e}") from e

        async with self.uow:
            result = await self.uow.rbac.update_role_name(role_id=cmd.role_id, name=name_vo)
            await self.uow.commit()

        return result
