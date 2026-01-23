from __future__ import annotations

from backend.application.common.dtos.users import GetUserWithRolesDTO, UserWithRolesDTO
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.storage import map_storage_error_to_app
from backend.application.common.interfaces.ports.persistence.gateway import PersistenceGateway
from backend.application.common.presenters.users import present_user_with_roles
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.result import Result
from backend.application.handlers.transform import handler


class GetUserWithRolesQuery(GetUserWithRolesDTO): ...


@handler(mode="read")
class GetUserWithRolesHandler(QueryHandler[GetUserWithRolesQuery, UserWithRolesDTO]):
    gateway: PersistenceGateway

    async def __call__(
        self,
        query: GetUserWithRolesQuery,
        /,
    ) -> Result[UserWithRolesDTO, AppError]:
        return (
            (await self.gateway.users.get_by_id(query.user_id))
            .map_err(map_storage_error_to_app)
            .map(present_user_with_roles)
        )
