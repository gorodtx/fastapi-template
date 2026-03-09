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
    present_users_by_role,
)
from backend.application.common.presenters.users import present_user_response
from backend.application.common.tools.read_tx_result import (
    run_result_in_read_tx,
)
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.result import Err, Result, ResultImpl
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
        return await run_result_in_read_tx(
            manager=self.gateway.manager,
            action_factory=lambda: self._execute(query),
        )

    async def _execute(
        self: GetUsersByRoleHandler,
        query: GetUsersByRoleQuery,
    ) -> Result[UsersByRoleResponseDTO, AppError]:
        role: RoleCode = query.role
        map_storage_error = map_storage_error_to_app()
        ids_result = (
            await self.gateway.rbac.list_user_ids_by_role(role)
        ).map_err(map_storage_error)
        if isinstance(ids_result, Err):
            return ResultImpl.err_from(ids_result)
        user_ids = ids_result.value

        users_result = (
            await self.gateway.users.get_by_ids(
                user_ids,
                include_roles=False,
            )
        ).map_err(map_storage_error)
        if isinstance(users_result, Err):
            return ResultImpl.err_from(users_result)

        users: list[UserResponseDTO] = [
            present_user_response(user) for user in users_result.value
        ]
        return ResultImpl.ok(present_users_by_role(role, users))
