from __future__ import annotations

from fastapi_backend.application.common.dtos.rbac_dto import RoleDeleteDTO
from fastapi_backend.application.common.exceptions.application import ResourceNotFoundError
from fastapi_backend.application.common.tools.handler_base import CommandHandler
from fastapi_backend.application.common.tools.handler_transform import handler
from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.ports.repositories.rbac_repository import RBACRepositoryPort
from fastapi_backend.domain.ports.unit_of_work import UnitOfWorkPort
from fastapi_backend.domain.services.rbac_domain_service import RBACDomainService


class DeleteRoleCommand(RoleDeleteDTO):
    role_id: str


@handler(mode="write")
class DeleteRoleHandler(CommandHandler[DeleteRoleCommand, None]):
    uow: UnitOfWorkPort
    rbac_repo: RBACRepositoryPort
    rbac_service: RBACDomainService

    async def _execute(self, cmd: DeleteRoleCommand, /) -> None:
        async with self.uow:
            role = await self.rbac_repo.find_role_by_id(TypeID(cmd.role_id))
            if not role:
                raise ResourceNotFoundError("Role", cmd.role_id)

            await self.rbac_service.delete_role(role)
            await self.rbac_repo.delete_role(role)
            await self.uow.commit()
