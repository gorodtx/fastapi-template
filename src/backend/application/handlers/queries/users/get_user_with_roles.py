from __future__ import annotations

from backend.application.common.dtos.users import (
    GetUserWithRolesDTO,
    UserWithRolesDTO,
)
from backend.application.common.exceptions.application import AppError
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.tools.user_access import (
    fetch_user_and_permissions,
)
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.result import Err, Result, ResultImpl
from backend.application.handlers.transform import handler


class GetUserWithRolesQuery(GetUserWithRolesDTO): ...


@handler(mode="read")
class GetUserWithRolesHandler(
    QueryHandler[GetUserWithRolesQuery, UserWithRolesDTO]
):
    gateway: PersistenceGateway

    async def __call__(
        self: GetUserWithRolesHandler,
        query: GetUserWithRolesQuery,
        /,
    ) -> Result[UserWithRolesDTO, AppError]:
        data_result = await fetch_user_and_permissions(
            self.gateway, query.user_id
        )
        if isinstance(data_result, Err):
            return ResultImpl.err_from(data_result)
        user, permissions_set = data_result.value

        permissions = sorted(
            permission.value for permission in permissions_set
        )
        roles = sorted(user.roles)
        return ResultImpl.ok(
            UserWithRolesDTO(
                id=user.id,
                email=user.email,
                login=user.login,
                username=user.username,
                roles=roles,
                permissions=permissions,
            )
        )
