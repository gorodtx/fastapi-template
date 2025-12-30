from __future__ import annotations

from backend.application.common.dtos.rbac import GetUsersByRoleDTO, UsersByRoleResponseDTO
from backend.application.common.exceptions.application import ConflictError
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.services.authorization import AuthorizationService
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.mappers import UserMapper
from backend.application.handlers.transform import handler
from backend.domain.core.constants.permission_codes import RBAC_READ_ROLES
from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.base import TypeID


class GetUsersByRoleQuery(GetUsersByRoleDTO):
    actor_id: TypeID
    role: str


@handler(mode="read")
class GetUsersByRoleHandler(QueryHandler[GetUsersByRoleQuery, UsersByRoleResponseDTO]):
    uow: UnitOfWorkPort
    authorization_service: AuthorizationService

    async def _execute(self, query: GetUsersByRoleQuery, /) -> UsersByRoleResponseDTO:
        async with self.uow:
            await self.authorization_service.require_permission(
                user_id=query.actor_id,
                permission=RBAC_READ_ROLES,
                rbac=self.uow.rbac,
            )
            try:
                role = SystemRole(query.role)
            except ValueError as exc:
                raise ConflictError(f"Unknown role {query.role!r}") from exc
            try:
                users = await self.uow.users.list_by_role(role=role)
            except LookupError as exc:
                raise ConflictError(f"Role {role.value!r} is not provisioned") from exc

        return UsersByRoleResponseDTO(role=role.value, users=UserMapper.to_many_dto(users))
