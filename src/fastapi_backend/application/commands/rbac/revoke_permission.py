from __future__ import annotations

from fastapi_backend.application.common.dtos.rbac_dto import RevokePermissionDTO
from fastapi_backend.application.common.exceptions.application import (
    ConflictError,
    ResourceNotFoundError,
)
from fastapi_backend.application.common.tools.handler_base import CommandHandler
from fastapi_backend.application.common.tools.handler_transform import handler
from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.core.exceptions.base import DomainError, DomainTypeError
from fastapi_backend.domain.core.value_objects.access.permission_code import PermissionCode
from fastapi_backend.domain.ports.repositories.rbac_repository import RBACRepositoryPort
from fastapi_backend.domain.ports.unit_of_work import UnitOfWorkPort
from fastapi_backend.domain.services.rbac_domain_service import RBACDomainService


class RevokePermissionCommand(RevokePermissionDTO):
    role_id: str
    permission: str


@handler(mode="write")
class RevokePermissionHandler(CommandHandler[RevokePermissionCommand, None]):
    uow: UnitOfWorkPort
    rbac_repo: RBACRepositoryPort
    rbac_service: RBACDomainService

    async def _execute(self, cmd: RevokePermissionCommand, /) -> None:
        async with self.uow:
            role = await self.rbac_repo.find_role_by_id(TypeID(cmd.role_id))
            if not role:
                raise ResourceNotFoundError("Role", cmd.role_id)

            try:
                permission = PermissionCode(cmd.permission)
            except (ValueError, DomainTypeError) as e:
                raise ConflictError(f"Invalid permission code: {e}") from e

            try:
                await self.rbac_service.revoke_permission(role, permission)
            except DomainError as e:
                raise ConflictError(f"Cannot revoke permission: {e}") from e

            await self.rbac_repo.save_role(role)
            await self.uow.commit()
