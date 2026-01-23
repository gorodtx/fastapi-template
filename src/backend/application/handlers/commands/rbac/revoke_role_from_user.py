from __future__ import annotations

from backend.application.common.dtos.rbac import RevokeRoleFromUserDTO, RoleAssignmentResultDTO
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.rbac import map_role_input_error
from backend.application.common.exceptions.error_mappers.storage import map_storage_error_to_app
from backend.application.common.interfaces.ports.persistence.gateway import PersistenceGateway
from backend.application.common.presenters.rbac import present_role_assignment_from
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import Result, ResultImpl, capture
from backend.application.handlers.transform import handler
from backend.domain.core.constants.rbac import SystemRole


class RevokeRoleFromUserCommand(RevokeRoleFromUserDTO): ...


@handler(mode="write")
class RevokeRoleFromUserHandler(CommandHandler[RevokeRoleFromUserCommand, RoleAssignmentResultDTO]):
    gateway: PersistenceGateway

    async def __call__(
        self,
        cmd: RevokeRoleFromUserCommand,
        /,
    ) -> Result[RoleAssignmentResultDTO, AppError]:
        def parse_role() -> SystemRole:
            return SystemRole(cmd.role)

        role_result = capture(
            parse_role,
            map_role_input_error(cmd.role, allow_unassigned=True),
        )
        if role_result.is_err():
            return ResultImpl.err_from(role_result)

        async with self.gateway.manager.transaction():
            user_result = (await self.gateway.users.get_by_id(cmd.user_id)).map_err(
                map_storage_error_to_app
            )
            if user_result.is_err():
                return ResultImpl.err_from(user_result)

            user = user_result.unwrap()
            role = role_result.unwrap()

            def revoke_role() -> None:
                user.revoke_role(role)

            revoke_result = capture(
                revoke_role,
                map_role_input_error(cmd.role, allow_unassigned=True),
            )
            if revoke_result.is_err():
                return ResultImpl.err_from(revoke_result)

            replace_result = (
                await self.gateway.rbac.replace_user_roles(user.id, set(user.roles))
            ).map_err(map_storage_error_to_app)
            if replace_result.is_err():
                return ResultImpl.err_from(replace_result)

            presenter = present_role_assignment_from(user.id, role)
            return replace_result.map(presenter)
