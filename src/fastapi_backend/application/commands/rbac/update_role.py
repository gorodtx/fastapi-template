from __future__ import annotations

from fastapi_backend.application.common.dtos.rbac_dto import (
    RoleResponseDTO,
    RoleUpdateDTO,
)
from fastapi_backend.application.common.exceptions.application import (
    ConflictError,
    ResourceNotFoundError,
)
from fastapi_backend.application.common.tools.handler_base import CommandHandler
from fastapi_backend.application.common.tools.handler_transform import handler
from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.core.exceptions.base import DomainError, DomainTypeError
from fastapi_backend.domain.core.value_objects.access.role_name import RoleName
from fastapi_backend.domain.ports.repositories.rbac_repository import RBACRepositoryPort
from fastapi_backend.domain.ports.unit_of_work import UnitOfWorkPort
from fastapi_backend.domain.services.rbac_domain_service import RBACDomainService


class UpdateRoleCommand(RoleUpdateDTO):
    role_id: str
    name: str | None = None
    description: str | None = None


@handler(mode="write")
class UpdateRoleHandler(CommandHandler[UpdateRoleCommand, RoleResponseDTO]):
    uow: UnitOfWorkPort
    rbac_repo: RBACRepositoryPort
    rbac_service: RBACDomainService

    async def _execute(self, cmd: UpdateRoleCommand, /) -> RoleResponseDTO:
        async with self.uow:
            role = await self.rbac_repo.find_role_by_id(TypeID(cmd.role_id))
            if not role:
                raise ResourceNotFoundError("Role", cmd.role_id)

            new_name = role.name
            if cmd.name:
                try:
                    new_name = RoleName(cmd.name)
                except (ValueError, DomainTypeError) as e:
                    raise ConflictError(f"Invalid role name: {e}") from e

                if cmd.name != role.name.value and await self.rbac_repo.exists_role_name(
                    new_name, exclude_id=role.id
                ):
                    raise ConflictError(f"Role {cmd.name!r} already exists")

            try:
                await self.rbac_service.update_role(
                    role, new_name, cmd.description or role.description
                )
            except DomainError as e:
                raise ConflictError(f"Cannot update role: {e}") from e

            await self.rbac_repo.save_role(role)
            await self.uow.commit()

        return RoleResponseDTO(
            id=role.id,
            name=role.name.value,
            description=role.description,
            permissions=[p.value for p in role.permissions],
            user_count=len(role.user_ids),
        )
