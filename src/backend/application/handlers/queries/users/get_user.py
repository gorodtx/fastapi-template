from __future__ import annotations

from backend.application.common.dtos.users import GetUserDTO, UserResponseDTO
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.presenters.users import present_user_response
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.result import Result
from backend.application.handlers.transform import handler


class GetUserQuery(GetUserDTO): ...


@handler(mode="read")
class GetUserHandler(QueryHandler[GetUserQuery, UserResponseDTO]):
    gateway: PersistenceGateway

    async def __call__(
        self: GetUserHandler, query: GetUserQuery, /
    ) -> Result[UserResponseDTO, AppError]:
        return (
            (
                await self.gateway.users.get_by_id(
                    query.user_id,
                    include_roles=False,
                )
            )
            .map_err(map_storage_error_to_app())
            .map(present_user_response)
        )
