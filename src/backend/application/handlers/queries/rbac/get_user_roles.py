from __future__ import annotations

from backend.application.common.dtos.rbac import (
    GetUserRolesDTO,
    UserRolesResponseDTO,
)
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.presenters.rbac import present_user_roles
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.result import Result, ResultImpl
from backend.application.handlers.transform import handler


class GetUserRolesQuery(GetUserRolesDTO): ...


@handler(mode="read")
class GetUserRolesHandler(
    QueryHandler[GetUserRolesQuery, UserRolesResponseDTO]
):
    gateway: PersistenceGateway

    async def __call__(
        self: GetUserRolesHandler,
        query: GetUserRolesQuery,
        /,
    ) -> Result[UserRolesResponseDTO, AppError]:
        user_result = (
            await self.gateway.users.get_by_id(query.user_id)
        ).map_err(map_storage_error_to_app())
        if user_result.is_err():
            return ResultImpl.err_from(user_result)
        user = user_result.unwrap()

        permissions_result = (
            await self.gateway.rbac.get_user_permission_codes(query.user_id)
        ).map_err(map_storage_error_to_app())
        if permissions_result.is_err():
            return ResultImpl.err_from(permissions_result)

        return ResultImpl.ok(
            present_user_roles(
                user_id=user.id,
                roles=user.roles,
                permissions=frozenset(permissions_result.unwrap()),
            ),
            AppError,
        )
