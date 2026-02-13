from __future__ import annotations

from backend.application.common.dtos.rbac import (
    RevokeRoleFromUserDTO,
    UserRolesResponseDTO,
)
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.rbac import (
    map_role_change_error,
    map_role_input_error,
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
    ensure_can_revoke_role,
    ensure_not_last_super_admin,
    ensure_not_self_role_change,
)
from backend.domain.core.services.users import revoke_user_role
from backend.domain.core.types.rbac import (
    RoleCode,
    validate_role_code,
)

_SUPER_ADMIN_ROLE: RoleCode = "super_admin"


class RevokeRoleFromUserCommand(RevokeRoleFromUserDTO): ...


@handler(mode="write")
class RevokeRoleFromUserHandler(
    CommandHandler[RevokeRoleFromUserCommand, UserRolesResponseDTO]
):
    gateway: PersistenceGateway

    async def __call__(
        self: RevokeRoleFromUserHandler,
        cmd: RevokeRoleFromUserCommand,
        /,
    ) -> Result[UserRolesResponseDTO, AppError]:
        async def action() -> UserRolesResponseDTO:
            def parse_role() -> RoleCode:
                return validate_role_code(cmd.role)

            role = capture(
                parse_role,
                map_role_input_error(cmd.role, allow_unassigned=True),
            ).unwrap()

            user = (
                (await self.gateway.users.get_by_id(cmd.user_id))
                .map_err(map_storage_error_to_app())
                .unwrap()
            )

            def enforce_policy() -> None:
                ensure_not_self_role_change(
                    actor_id=cmd.actor_id,
                    target_user_id=user.id,
                    action=RoleAction.REVOKE,
                )
                ensure_can_revoke_role(set(cmd.actor_roles), role)

            capture(
                enforce_policy,
                map_role_change_error(
                    action=RoleAction.REVOKE, target_role=role
                ),
            ).unwrap()

            if role == _SUPER_ADMIN_ROLE and _SUPER_ADMIN_ROLE in user.roles:
                user_ids = (
                    (await self.gateway.rbac.list_user_ids_by_role(role))
                    .map_err(map_storage_error_to_app())
                    .unwrap()
                )
                remaining_super_admins = len(
                    [uid for uid in user_ids if uid != user.id]
                )

                def ensure_last_super_admin() -> None:
                    ensure_not_last_super_admin(
                        target_user_id=user.id,
                        remaining_super_admins=remaining_super_admins,
                    )

                capture(
                    ensure_last_super_admin,
                    map_role_change_error(
                        action=RoleAction.REVOKE, target_role=role
                    ),
                ).unwrap()

            capture(
                lambda: revoke_user_role(user, role),
                map_role_change_error(
                    action=RoleAction.REVOKE, target_role=role
                ),
            ).unwrap()

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
