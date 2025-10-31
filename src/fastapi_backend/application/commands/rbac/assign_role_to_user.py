from __future__ import annotations

from fastapi_backend.application.common.dtos.rbac_dto import AssignRoleToUserDTO
from fastapi_backend.application.common.exceptions.application import (
    ConflictError,
    ResourceNotFoundError,
)
from fastapi_backend.application.common.tools.handler_base import CommandHandler
from fastapi_backend.application.common.tools.handler_transform import handler
from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.core.exceptions.base import DomainError
from fastapi_backend.domain.ports.repositories.rbac_repository import RBACRepositoryPort
from fastapi_backend.domain.ports.repositories.user_repository import UserRepositoryPort
from fastapi_backend.domain.ports.unit_of_work import UnitOfWorkPort
from fastapi_backend.domain.services.rbac_domain_service import RBACDomainService


class AssignRoleToUserCommand(AssignRoleToUserDTO):
    role_id: str
    user_id: str


@handler(mode="write")
class AssignRoleToUserHandler(CommandHandler[AssignRoleToUserCommand, None]):
    uow: UnitOfWorkPort
    rbac_repo: RBACRepositoryPort
    user_repo: UserRepositoryPort
    rbac_service: RBACDomainService

    async def _execute(self, cmd: AssignRoleToUserCommand, /) -> None:
        async with self.uow:
            role_id = TypeID(cmd.role_id)
            user_id = TypeID(cmd.user_id)

            role = await self.rbac_repo.find_role_by_id(role_id)
            if not role:
                raise ResourceNotFoundError("Role", cmd.role_id)

            user = await self.user_repo.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", cmd.user_id)

            try:
                await self.rbac_service.assign_role_to_user(role, user_id)
            except DomainError as e:
                raise ConflictError(f"Cannot assign role: {e}") from e

            await self.rbac_repo.save_role(role)
            await self.uow.commit()
