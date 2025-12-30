from __future__ import annotations

from backend.application.common.dtos.rbac import GetUserRolesDTO, UserRolesResponseDTO
from backend.application.common.exceptions.application import ResourceNotFoundError
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.services.authorization import AuthorizationService
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.transform import handler
from backend.domain.core.constants.permission_codes import RBAC_READ_ROLES
from backend.domain.core.entities.base import TypeID
from backend.domain.core.services.access_control import permissions_for_roles


class GetUserRolesQuery(GetUserRolesDTO):
    actor_id: TypeID
    user_id: TypeID


@handler(mode="read")
class GetUserRolesHandler(QueryHandler[GetUserRolesQuery, UserRolesResponseDTO]):
    uow: UnitOfWorkPort
    authorization_service: AuthorizationService

    async def _execute(self, query: GetUserRolesQuery, /) -> UserRolesResponseDTO:
        async with self.uow:
            await self.authorization_service.require_permission(
                user_id=query.actor_id,
                permission=RBAC_READ_ROLES,
                rbac=self.uow.rbac,
            )
            try:
                await self.uow.users.get_one(user_id=query.user_id)
            except LookupError as exc:
                raise ResourceNotFoundError("User", str(query.user_id)) from exc
            roles = await self.uow.rbac.list_user_roles(user_id=query.user_id)

        permissions = permissions_for_roles(roles)
        return UserRolesResponseDTO(
            user_id=query.user_id,
            roles=sorted(role.value for role in roles),
            permissions=sorted(permission.value for permission in permissions),
        )
