from __future__ import annotations

from backend.application.common.dtos.rbac import (
    AssignRoleToUserDTO,
    RoleAssignmentResultDTO,
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
    present_role_assignment_from,
)
from backend.application.common.tools.auth_cache import AuthCacheInvalidator
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import Result, ResultImpl, capture
from backend.application.handlers.transform import handler
from backend.domain.core.constants.rbac import RoleAction, SystemRole
from backend.domain.core.services.access_control import (
    ensure_can_assign_role,
    ensure_not_self_role_change,
)


class AssignRoleToUserCommand(AssignRoleToUserDTO): ...


@handler(mode="write")
class AssignRoleToUserHandler(
    CommandHandler[AssignRoleToUserCommand, RoleAssignmentResultDTO]
):
    gateway: PersistenceGateway
    cache_invalidator: AuthCacheInvalidator

    async def __call__(
        self: AssignRoleToUserHandler,
        cmd: AssignRoleToUserCommand,
        /,
    ) -> Result[RoleAssignmentResultDTO, AppError]:
        def parse_role() -> SystemRole:
            return SystemRole(cmd.role)

        role_result = capture(parse_role, map_role_input_error(cmd.role))
        if role_result.is_err():
            return ResultImpl.err_from(role_result)

        async with self.gateway.manager.transaction():
            user_result = (
                await self.gateway.users.get_by_id(cmd.user_id)
            ).map_err(map_storage_error_to_app())
            if user_result.is_err():
                return ResultImpl.err_from(user_result)

            actor_result = (
                await self.gateway.users.get_by_id(cmd.actor_id)
            ).map_err(map_storage_error_to_app())
            if actor_result.is_err():
                return ResultImpl.err_from(actor_result)

            user = user_result.unwrap()
            actor = actor_result.unwrap()
            role = role_result.unwrap()

            def enforce_policy() -> None:
                ensure_not_self_role_change(
                    actor_id=cmd.actor_id,
                    target_user_id=user.id,
                    action=RoleAction.ASSIGN,
                )
                ensure_can_assign_role(set(actor.roles), role)

            policy_result = capture(
                enforce_policy,
                map_role_change_error(
                    action=RoleAction.ASSIGN, target_role=role
                ),
            )
            if policy_result.is_err():
                return ResultImpl.err_from(policy_result)

            def assign_role() -> None:
                user.assign_role(role)

            assign_result = capture(
                assign_role,
                map_role_change_error(
                    action=RoleAction.ASSIGN, target_role=role
                ),
            )
            if assign_result.is_err():
                return ResultImpl.err_from(assign_result)

            replace_result = (
                await self.gateway.rbac.replace_user_roles(
                    user.id, set(user.roles)
                )
            ).map_err(map_storage_error_to_app())
            if replace_result.is_err():
                return ResultImpl.err_from(replace_result)

            presenter = present_role_assignment_from(user.id, role)
            response = replace_result.map(presenter)

        await self.cache_invalidator.invalidate_user(cmd.user_id)
        return response
