from __future__ import annotations

from backend.application.common.dtos.rbac import (
    AssignRoleToUserDTO,
    UserRolesResponseDTO,
)
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.rbac import (
    map_role_change_error,
)
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.presenters.rbac import (
    present_user_roles,
)
from backend.application.common.tools.tx_result import run_result_in_tx
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import (
    Err,
    Result,
    ResultImpl,
    capture,
)
from backend.application.handlers.transform import handler
from backend.domain.core.constants.rbac import RoleAction
from backend.domain.core.services.access_control import (
    ensure_can_assign_role,
    ensure_not_self_role_change,
)
from backend.domain.core.types.rbac import RoleCode


class AssignRoleToUserCommand(AssignRoleToUserDTO): ...


@handler(mode="write")
class AssignRoleToUserHandler(
    CommandHandler[AssignRoleToUserCommand, UserRolesResponseDTO]
):
    gateway: PersistenceGateway

    async def __call__(
        self: AssignRoleToUserHandler,
        cmd: AssignRoleToUserCommand,
        /,
    ) -> Result[UserRolesResponseDTO, AppError]:
        return await run_result_in_tx(
            manager=self.gateway.manager,
            action_factory=lambda: self._execute(cmd),
        )

    async def _execute(
        self: AssignRoleToUserHandler,
        cmd: AssignRoleToUserCommand,
    ) -> Result[UserRolesResponseDTO, AppError]:
        role: RoleCode = cmd.role

        user_result = (
            await self.gateway.users.get_by_id(cmd.user_id)
        ).map_err(map_storage_error_to_app())
        if isinstance(user_result, Err):
            return ResultImpl.err_from(user_result)
        user = user_result.value

        map_change_error = map_role_change_error(
            action=RoleAction.ASSIGN, target_role=role
        )
        self_change_result = capture(
            lambda: ensure_not_self_role_change(
                actor_id=cmd.actor_id,
                target_user_id=user.id,
                action=RoleAction.ASSIGN,
            ),
            map_change_error,
        )
        if isinstance(self_change_result, Err):
            return ResultImpl.err_from(self_change_result)

        role_guard_result = capture(
            lambda: ensure_can_assign_role(set(cmd.actor_roles), role),
            map_change_error,
        )
        if isinstance(role_guard_result, Err):
            return ResultImpl.err_from(role_guard_result)

        user.roles.add(role)

        replace_roles_result = (
            await self.gateway.rbac.replace_user_roles(
                user.id, set(user.roles)
            )
        ).map_err(map_storage_error_to_app())
        if isinstance(replace_roles_result, Err):
            return ResultImpl.err_from(replace_roles_result)

        permissions_result = (
            await self.gateway.rbac.get_user_permission_codes(user.id)
        ).map_err(map_storage_error_to_app())
        if isinstance(permissions_result, Err):
            return ResultImpl.err_from(permissions_result)

        return ResultImpl.ok(
            present_user_roles(
                user_id=user.id,
                roles=frozenset(user.roles),
                permissions=frozenset(permissions_result.value),
            ),
        )
