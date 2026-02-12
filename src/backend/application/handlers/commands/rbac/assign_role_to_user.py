from __future__ import annotations

from backend.application.common.dtos.rbac import (
    AssignRoleToUserDTO,
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
    ensure_can_assign_role,
    ensure_not_self_role_change,
)
from backend.domain.core.types.rbac import (
    RoleCode,
    validate_role_code,
)


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
        def parse_role() -> RoleCode:
            return validate_role_code(cmd.role)

        role_result = capture(parse_role, map_role_input_error(cmd.role))
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
                action=RoleAction.ASSIGN,
            )
            ensure_can_assign_role(set(cmd.actor_roles), role)

        policy_result = capture(
            enforce_policy,
            map_role_change_error(action=RoleAction.ASSIGN, target_role=role),
        )
        if policy_result.is_err():
            return ResultImpl.err_from(policy_result)

        user.roles.add(role)

        replace_result = (
            await self.gateway.rbac.replace_user_roles(
                user.id, set(user.roles)
            )
        ).map_err(map_storage_error_to_app())
        if replace_result.is_err():
            return ResultImpl.err_from(replace_result)

        permissions_result = (
            await self.gateway.rbac.get_user_permission_codes(user.id)
        ).map_err(map_storage_error_to_app())
        if permissions_result.is_err():
            return ResultImpl.err_from(permissions_result)

        response = ResultImpl.ok(
            present_user_roles(
                user_id=user.id,
                roles=frozenset(user.roles),
                permissions=frozenset(permissions_result.unwrap()),
            ),
            AppError,
        )
        return response
