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
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import Result, ResultImpl, capture
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
    normalize_role_code,
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
        def parse_role() -> RoleCode:
            return validate_role_code(normalize_role_code(cmd.role))

        role_result = capture(
            parse_role,
            map_role_input_error(cmd.role, allow_unassigned=True),
        )
        if role_result.is_err():
            return ResultImpl.err_from(role_result)

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
            map_role_change_error(action=RoleAction.REVOKE, target_role=role),
        )
        if policy_result.is_err():
            return ResultImpl.err_from(policy_result)

        if role == _SUPER_ADMIN_ROLE and _SUPER_ADMIN_ROLE in user.roles:
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

        revoke_result = capture(
            lambda: revoke_user_role(user, role),
            map_role_change_error(action=RoleAction.REVOKE, target_role=role),
        )
        if revoke_result.is_err():
            return ResultImpl.err_from(revoke_result)

        replace_result = (
            await self.gateway.rbac.replace_user_roles(
                user.id, set(user.roles)
            )
        ).map_err(map_storage_error_to_app())

        permissions_result = (
            await self.gateway.rbac.get_user_permission_codes(user.id)
        ).map_err(map_storage_error_to_app())

        def failed_error_or_none() -> AppError | None:
            if replace_result.is_err():
                return replace_result.unwrap_err()
            if permissions_result.is_err():
                return permissions_result.unwrap_err()
            return None

        failed_error = failed_error_or_none()
        if failed_error is not None:
            return ResultImpl.err(failed_error)

        response = ResultImpl.ok(
            present_user_roles(
                user_id=user.id,
                roles=frozenset(user.roles),
                permissions=frozenset(permissions_result.unwrap()),
            ),
            AppError,
        )
        return response
