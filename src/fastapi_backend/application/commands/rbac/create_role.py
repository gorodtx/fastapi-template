from __future__ import annotations

from fastapi_backend.application.common.dtos.rbac_dto import (
    RoleCreateDTO,
    RoleResponseDTO,
)
from fastapi_backend.application.common.exceptions.application import ConflictError
from fastapi_backend.application.common.tools.handler_base import CommandHandler
from fastapi_backend.application.common.tools.handler_transform import handler
from fastapi_backend.domain.core.exceptions.base import DomainError, DomainTypeError
from fastapi_backend.domain.core.exceptions.rbac import RoleAlreadyExistsError
from fastapi_backend.domain.core.value_objects.identity.role_name import RoleName
from fastapi_backend.domain.ports.repositories.rbac_repository import RBACRepositoryPort
from fastapi_backend.domain.ports.unit_of_work import UnitOfWorkPort
from fastapi_backend.domain.services.rbac_domain_service import RBACDomainService


class CreateRoleCommand(RoleCreateDTO):
    name: str
    description: str | None = None


@handler(mode="write")
class CreateRoleHandler(CommandHandler[CreateRoleCommand, RoleResponseDTO]):
    uow: UnitOfWorkPort
    rbac_repo: RBACRepositoryPort
    rbac_service: RBACDomainService

    async def _execute(self, cmd: CreateRoleCommand, /) -> RoleResponseDTO:
        async with self.uow:
            try:
                role_name = RoleName(cmd.name)
            except (ValueError, DomainTypeError) as e:
                raise ConflictError(f"Invalid role name: {e}") from e

            if await self.rbac_repo.exists_role_name(role_name):
                raise ConflictError(f"Role {cmd.name!r} already exists")

            try:
                role = await self.rbac_service.create_role(role_name, cmd.description)
            except RoleAlreadyExistsError as e:
                raise ConflictError(str(e)) from e
            except DomainError as e:
                raise ConflictError(f"Cannot create role: {e}") from e

            await self.rbac_repo.save_role(role)
            await self.uow.commit()

        return RoleResponseDTO(
            id=role.id,
            name=role.name.value,
            description=role.description,
            permissions=[p.value for p in role.permissions],
            user_count=len(role.user_ids),
        )
