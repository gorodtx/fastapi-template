from backend.application.common.dtos.users import GetUserDTO, UserResponseDTO
from backend.application.common.exceptions.application import ResourceNotFoundError
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.tools.handler_base import QueryHandler
from backend.application.common.tools.handler_transform import handler


class GetUserQuery(GetUserDTO): ...


@handler(mode="read")
class GetUserHandler(QueryHandler[GetUserQuery, UserResponseDTO]):
    uow: UnitOfWorkPort

    async def _execute(self, query: GetUserQuery, /) -> UserResponseDTO:
        async with self.uow:
            dto = await self.uow.users.get_one(user_id=query.user_id)

        if dto is None:
            raise ResourceNotFoundError("User", str(query.user_id))

        return dto
