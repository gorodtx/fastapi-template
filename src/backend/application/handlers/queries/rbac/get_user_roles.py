from __future__ import annotations

from backend.application.common.dtos.rbac import GetUserRolesDTO, UserRolesResponseDTO
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.storage import map_storage_error_to_app
from backend.application.common.interfaces.infra.persistence.gateway import PersistenceGateway
from backend.application.common.presenters.rbac import present_user_roles
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.result import Result
from backend.application.handlers.transform import handler


class GetUserRolesQuery(GetUserRolesDTO): ...


@handler(mode="read")
class GetUserRolesHandler(QueryHandler[GetUserRolesQuery, UserRolesResponseDTO]):
    gateway: PersistenceGateway

    async def __call__(
        self,
        query: GetUserRolesQuery,
        /,
    ) -> Result[UserRolesResponseDTO, AppError]:
        return (
            (await self.gateway.users.get_by_id(query.user_id))
            .map_err(map_storage_error_to_app)
            .map(present_user_roles)
        )
