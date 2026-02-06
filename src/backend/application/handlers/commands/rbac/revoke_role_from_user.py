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
from backend.application.common.tools.auth_cache import AuthCacheInvalidator
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import Result, ResultImpl, capture
from backend.application.handlers.transform import handler
from backend.domain.core.constants.rbac import RoleAction, SystemRole
from backend.domain.core.services.access_control import (
    ensure_can_revoke_role,
    ensure_not_last_super_admin,
    ensure_not_self_role_change,
)


class RevokeRoleFromUserCommand(RevokeRoleFromUserDTO): ...


@handler(mode="write")
class RevokeRoleFromUserHandler(
    CommandHandler[RevokeRoleFromUserCommand, UserRolesResponseDTO]
):
    gateway: PersistenceGateway
    cache_invalidator: AuthCacheInvalidator

    async def __call__(
        self: RevokeRoleFromUserHandler,
        cmd: RevokeRoleFromUserCommand,
        /,
    ) -> Result[UserRolesResponseDTO, AppError]:
        def parse_role() -> SystemRole:
            return SystemRole(cmd.role)

        role_result = capture(
            parse_role,
            map_role_input_error(cmd.role, allow_unassigned=True),
        )
        if role_result.is_err():
            return ResultImpl.err_from(role_result)

        async with self.gateway.manager.transaction():
            user_result = (
                await self.gateway.users.get_by_id(cmd.user_id)
            ).map_err(map_storage_error_to_app())
            if user_result.is_err():
                return ResultImpl.err_from(user_result)

            user = user_result.unwrap()
            role = role_result.unwrap()

            def enforce_policy() -> None:
                ensure_not_self_role_change(
                    actor_id=cmd.actor_id,
                    target_user_id=user.id,
                    action=RoleAction.REVOKE,
                )
                ensure_can_revoke_role(set(cmd.actor_roles), role)

            policy_result = capture(
                enforce_policy,
                map_role_change_error(
                    action=RoleAction.REVOKE, target_role=role
                ),
            )
            if policy_result.is_err():
                return ResultImpl.err_from(policy_result)

            if (
                role == SystemRole.SUPER_ADMIN
                and SystemRole.SUPER_ADMIN in user.roles
            ):
                ids_result = (
                    await self.gateway.rbac.list_user_ids_by_role(role)
                ).map_err(map_storage_error_to_app())
                if ids_result.is_err():
                    return ResultImpl.err_from(ids_result)
                remaining = len(
                    [uid for uid in ids_result.unwrap() if uid != user.id]
                )

                def ensure_last_super_admin() -> None:
                    ensure_not_last_super_admin(
                        target_user_id=user.id,
                        remaining_super_admins=remaining,
                    )

                last_super_admin_result = capture(
                    ensure_last_super_admin,
                    map_role_change_error(
                        action=RoleAction.REVOKE, target_role=role
                    ),
                )
                if last_super_admin_result.is_err():
                    return ResultImpl.err_from(last_super_admin_result)

            def revoke_role() -> None:
                user.revoke_role(role)

            revoke_result = capture(
                revoke_role,
                map_role_change_error(
                    action=RoleAction.REVOKE, target_role=role
                ),
            )
            if revoke_result.is_err():
                return ResultImpl.err_from(revoke_result)

            replace_result = (
                await self.gateway.rbac.replace_user_roles(
                    user.id, set(user.roles)
                )
            ).map_err(map_storage_error_to_app())
            if replace_result.is_err():
                return ResultImpl.err_from(replace_result)

            response = ResultImpl.ok(present_user_roles(user), AppError)

        await self.cache_invalidator.invalidate_user(cmd.user_id)
        return response
