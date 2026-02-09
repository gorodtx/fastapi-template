from __future__ import annotations

from backend.application.common.dtos.users import (
    GetUserWithRolesDTO,
    UserWithRolesDTO,
)
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.result import Result, ResultImpl
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

        permissions = sorted(
            permission.value for permission in permissions_result.unwrap()
        )
        roles = sorted(role.value for role in user.roles)
        return ResultImpl.ok(
            UserWithRolesDTO(
                id=user.id,
                email=user.email.value,
                login=user.login.value,
                username=user.username.value,
                roles=roles,
                permissions=permissions,
            ),
            AppError,
        )
