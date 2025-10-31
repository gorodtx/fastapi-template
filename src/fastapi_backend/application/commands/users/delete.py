from __future__ import annotations

from fastapi_backend.application.common.dtos.users_dto import DeleteUserDTO
from fastapi_backend.application.common.tools.handler_base import CommandHandler
from fastapi_backend.application.common.tools.handler_transform import handler
from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.ports.repositories.user_repository import UserRepositoryPort
from fastapi_backend.domain.ports.unit_of_work import UnitOfWorkPort


class DeleteUserCommand(DeleteUserDTO):
    user_id: str


@handler(mode="write")
class DeleteUserHandler(CommandHandler[DeleteUserCommand, None]):
    uow: UnitOfWorkPort
    user_repo: UserRepositoryPort

    async def _execute(self, cmd: DeleteUserCommand, /) -> None:
        async with self.uow:
            uid = TypeID(cmd.user_id)
            user = await self.user_repo.find_by_id(uid)
            if not user:
                raise LookupError(f"User {cmd.user_id!r} not found")

            await self.user_repo.delete(user)
            await self.uow.commit()
