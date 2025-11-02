from __future__ import annotations

from fastapi_backend.application.common.dtos.users_dto import GetUserDTO, UserResponseDTO
from fastapi_backend.application.common.tools.handler_base import QueryHandler
from fastapi_backend.application.common.tools.handler_transform import handler
from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.ports.repositories.user_repository import UserRepositoryPort


class GetUserQuery(GetUserDTO):
    user_id: str


@handler(mode="read")
class GetUserHandler(QueryHandler[GetUserQuery, UserResponseDTO]):
    user_repo: UserRepositoryPort

    async def _execute(self, query: GetUserQuery, /) -> UserResponseDTO:
        user = await self.user_repo.find_by_id(TypeID(query.user_id))
        if not user:
            raise LookupError(f"User {query.user_id!r} not found")

        return UserResponseDTO(id=user.id, email=user.email.value, is_active=True)
