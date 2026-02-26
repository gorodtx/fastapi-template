from __future__ import annotations

from backend.application.common.dtos.rbac import (
    RevokeRoleFromUserDTO,
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
    ensure_can_revoke_role,
    ensure_not_last_super_admin,
    ensure_not_self_role_change,
)
from backend.domain.core.services.users import revoke_user_role
from backend.domain.core.types.rbac import RoleCode

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
        return await run_result_in_tx(
            manager=self.gateway.manager,
            action_factory=lambda: self._execute(cmd),
        )

    async def _execute(
        self: RevokeRoleFromUserHandler,
        cmd: RevokeRoleFromUserCommand,
    ) -> Result[UserRolesResponseDTO, AppError]:
        role: RoleCode = cmd.role

        user_result = (
            await self.gateway.users.lock_by_id(cmd.user_id)
        ).map_err(map_storage_error_to_app())
        if isinstance(user_result, Err):
            return ResultImpl.err_from(user_result)
        user = user_result.value

        map_change_error = map_role_change_error(
            action=RoleAction.REVOKE, target_role=role
        )
        self_change_result = capture(
            lambda: ensure_not_self_role_change(
                actor_id=cmd.actor_id,
                target_user_id=user.id,
                action=RoleAction.REVOKE,
            ),
            map_change_error,
        )
        role_guard_result = capture(
            lambda: ensure_can_revoke_role(set(cmd.actor_roles), role),
            map_change_error,
        )
        for guard_result in (self_change_result, role_guard_result):
            if isinstance(guard_result, Err):
                return ResultImpl.err_from(guard_result)

        if role == _SUPER_ADMIN_ROLE and _SUPER_ADMIN_ROLE in user.roles:
            user_ids_result = (
                await self.gateway.rbac.list_user_ids_by_role(role)
            ).map_err(map_storage_error_to_app())
            if isinstance(user_ids_result, Err):
                return ResultImpl.err_from(user_ids_result)

            remaining_super_admins = len(
                [uid for uid in user_ids_result.value if uid != user.id]
            )
            super_admin_guard_result = capture(
                lambda: ensure_not_last_super_admin(
                    target_user_id=user.id,
                    remaining_super_admins=remaining_super_admins,
                ),
                map_change_error,
            )
            if isinstance(super_admin_guard_result, Err):
                return ResultImpl.err_from(super_admin_guard_result)

        revoke_result = capture(
            lambda: revoke_user_role(user, role),
            map_change_error,
        )
        if isinstance(revoke_result, Err):
            return ResultImpl.err_from(revoke_result)

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
