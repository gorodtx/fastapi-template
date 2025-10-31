from __future__ import annotations

from fastapi_backend.application.common.dtos.rbac_dto import GetRoleDTO, RoleResponseDTO
from fastapi_backend.application.common.exceptions.application import ResourceNotFoundError
from fastapi_backend.application.common.tools.handler_base import QueryHandler
from fastapi_backend.application.common.tools.handler_transform import handler
from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.ports.repositories.rbac_repository import RBACRepositoryPort


class GetRoleQuery(GetRoleDTO):
    role_id: str


@handler(mode="read")
class GetRoleHandler(QueryHandler[GetRoleQuery, RoleResponseDTO]):
    rbac_repo: RBACRepositoryPort

    async def _execute(self, query: GetRoleQuery, /) -> RoleResponseDTO:
        role = await self.rbac_repo.find_role_by_id(TypeID(query.role_id))
        if not role:
            raise ResourceNotFoundError("Role", query.role_id)

        return RoleResponseDTO(
            id=role.id,
            name=role.name.value,
            description=role.description,
            permissions=[p.value for p in role.permissions],
            user_count=len(role.user_ids),
        )
