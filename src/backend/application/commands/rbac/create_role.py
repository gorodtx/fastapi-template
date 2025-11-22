from __future__ import annotations

import uuid_utils.compat as uuid

from backend.application.common.dtos.rbac import (
    RoleCreateDTO,
    RoleResponseDTO,
)
from backend.application.common.exceptions.application import ConflictError
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.tools.handler_base import CommandHandler
from backend.application.common.tools.handler_transform import handler
from backend.domain.core.entities.role import Role
from backend.domain.core.exceptions.base import DomainTypeError
from backend.domain.core.value_objects.identity.role_name import RoleName


class CreateRoleCommand(RoleCreateDTO):
    name: str
    description: str | None = None


@handler(mode="write")
class CreateRoleHandler(CommandHandler[CreateRoleCommand, RoleResponseDTO]):
    uow: UnitOfWorkPort

    async def _execute(self, cmd: CreateRoleCommand, /) -> RoleResponseDTO:
        try:
            role = Role.create(id=uuid.uuid7(), name=RoleName(cmd.name))
        except (ValueError, DomainTypeError) as e:
            raise ConflictError(f"Invalid role name: {e}") from e

        async with self.uow:
            result = await self.uow.rbac.create_role(role)
            await self.uow.commit()

        return result
