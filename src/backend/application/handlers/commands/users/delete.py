from __future__ import annotations

from backend.application.common.dtos.users import DeleteUserDTO, UserResponseDTO
from backend.application.common.exceptions.db import ConstraintViolationError
from backend.application.common.exceptions.infra_mapper import map_infra_error_to_application
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.services.authorization import AuthorizationService
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.mappers import UserMapper
from backend.application.handlers.transform import handler
from backend.domain.core.constants.permission_codes import USERS_DELETE
from backend.domain.core.entities.base import TypeID


class DeleteUserCommand(DeleteUserDTO):
    actor_id: TypeID
    user_id: TypeID


@handler(mode="write")
class DeleteUserHandler(CommandHandler[DeleteUserCommand, UserResponseDTO]):
    uow: UnitOfWorkPort
    authorization_service: AuthorizationService

    async def _execute(self, cmd: DeleteUserCommand, /) -> UserResponseDTO:
        async with self.uow:
            await self.authorization_service.require_permission(
                user_id=cmd.actor_id,
                permission=USERS_DELETE,
                rbac=self.uow.rbac,
            )
            result = await self.uow.users.delete(user_id=cmd.user_id)
            try:
                await self.uow.commit()
            except ConstraintViolationError as exc:
                raise map_infra_error_to_application(exc) from exc

        return UserMapper.to_dto(result)
