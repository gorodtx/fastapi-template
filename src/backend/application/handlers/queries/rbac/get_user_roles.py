from __future__ import annotations

from backend.application.common.dtos.rbac import (
    GetUserRolesDTO,
    UserRolesResponseDTO,
)
from backend.application.common.exceptions.application import AppError
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.presenters.rbac import present_user_roles
from backend.application.common.tools.user_access import (
    fetch_user_and_permissions,
)
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
        data_result = await fetch_user_and_permissions(
            self.gateway, query.user_id
        )
        if data_result.is_err():
            return ResultImpl.err_from(data_result)
        user, permissions = data_result.unwrap()

        return ResultImpl.ok(
            present_user_roles(
                user_id=user.id,
                roles=frozenset(user.roles),
                permissions=frozenset(permissions),
            ),
            AppError,
        )
