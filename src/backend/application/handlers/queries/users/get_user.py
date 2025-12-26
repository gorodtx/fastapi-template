from __future__ import annotations

from backend.application.common.dtos.users import GetUserDTO, UserResponseDTO
from backend.application.common.exceptions.application import ResourceNotFoundError
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.services.authorization import AuthorizationService
from backend.application.handlers.base import QueryHandler
from backend.application.handlers.mappers import UserMapper
from backend.application.handlers.transform import handler
from backend.domain.core.constants.permission_codes import USERS_READ
from backend.domain.core.entities.base import TypeID


class GetUserQuery(GetUserDTO):
    actor_id: TypeID
    user_id: TypeID


@handler(mode="read")
class GetUserHandler(QueryHandler[GetUserQuery, UserResponseDTO]):
    uow: UnitOfWorkPort
    authorization_service: AuthorizationService

    async def _execute(self, query: GetUserQuery, /) -> UserResponseDTO:
        async with self.uow:
            await self.authorization_service.require_permission(
                user_id=query.actor_id,
                permission=USERS_READ,
                rbac=self.uow.rbac,
            )
            try:
                entity = await self.uow.users.get_one(user_id=query.user_id)
            except LookupError as exc:
                raise ResourceNotFoundError("User", str(query.user_id)) from exc

        return UserMapper.to_dto(entity)
