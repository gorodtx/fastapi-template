from __future__ import annotations

from backend.application.common.dtos.rbac import (
    GetUsersByRoleDTO,
    UsersByRoleResponseDTO,
)
from backend.application.common.dtos.users import UserResponseDTO
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.presenters.rbac import (
    present_users_by_role_from,
)
from backend.application.common.presenters.users import present_user_response
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.result import Result, ResultImpl
from backend.application.handlers.transform import handler
from backend.domain.core.types.rbac import RoleCode


class GetUsersByRoleQuery(GetUsersByRoleDTO): ...


@handler(mode="read")
class GetUsersByRoleHandler(
    QueryHandler[GetUsersByRoleQuery, UsersByRoleResponseDTO]
):
    gateway: PersistenceGateway

    async def __call__(
        self: GetUsersByRoleHandler,
        query: GetUsersByRoleQuery,
        /,
    ) -> Result[UsersByRoleResponseDTO, AppError]:
        role: RoleCode = query.role
        ids_result = (
            await self.gateway.rbac.list_user_ids_by_role(role)
        ).map_err(map_storage_error_to_app())
        if ids_result.is_err():
            return ResultImpl.err_from(ids_result)

        users: list[UserResponseDTO] = []
        for user_id in ids_result.unwrap():
            user_result = (
                await self.gateway.users.get_by_id(user_id)
            ).map_err(map_storage_error_to_app())
            if user_result.is_err():
                return ResultImpl.err_from(user_result)
            users.append(present_user_response(user_result.unwrap()))

        presenter = present_users_by_role_from(role, users)
        return ids_result.map(presenter)
