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
from backend.application.common.tools.tx_result import run_in_tx
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import Result, capture
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
        async def action() -> UserRolesResponseDTO:
            role: RoleCode = cmd.role

            user = (
                (await self.gateway.users.get_by_id(cmd.user_id))
                .map_err(map_storage_error_to_app())
                .unwrap()
            )

            map_change_error = map_role_change_error(
                action=RoleAction.ASSIGN, target_role=role
            )
            capture(
                lambda: ensure_not_self_role_change(
                    actor_id=cmd.actor_id,
                    target_user_id=user.id,
                    action=RoleAction.ASSIGN,
                ),
                map_change_error,
            ).unwrap()
            capture(
                lambda: ensure_can_assign_role(set(cmd.actor_roles), role),
                map_change_error,
            ).unwrap()

            user.roles.add(role)

            (
                await self.gateway.rbac.replace_user_roles(
                    user.id, set(user.roles)
                )
            ).map_err(map_storage_error_to_app()).unwrap()

            permissions = (
                (await self.gateway.rbac.get_user_permission_codes(user.id))
                .map_err(map_storage_error_to_app())
                .unwrap()
            )

            return present_user_roles(
                user_id=user.id,
                roles=frozenset(user.roles),
                permissions=frozenset(permissions),
            )

        return await run_in_tx(
            manager=self.gateway.manager,
            action=action,
            value_type=UserRolesResponseDTO,
        )
