from backend.application.common.dtos.rbac import GetRoleDTO, RoleResponseDTO
from backend.application.common.exceptions.application import ResourceNotFoundError
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.tools.handler_base import QueryHandler
from backend.application.common.tools.handler_transform import handler


class GetRoleQuery(GetRoleDTO): ...


@handler(mode="read")
class GetRoleHandler(QueryHandler[GetRoleQuery, RoleResponseDTO]):
    uow: UnitOfWorkPort

    async def _execute(self, query: GetRoleQuery, /) -> RoleResponseDTO:
        async with self.uow:
            dto = await self.uow.rbac.get_role(role_id=query.role_id)

        if dto is None:
            raise ResourceNotFoundError("Role", str(query.role_id))

        return dto
