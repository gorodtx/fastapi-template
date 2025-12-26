from __future__ import annotations

from backend.application.common.dtos.rbac import RevokeRoleFromUserDTO, RoleAssignmentResultDTO
from backend.application.common.exceptions.application import (
    ConflictError,
    ResourceNotFoundError,
    RoleHierarchyViolationError,
)
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.services.authorization import AuthorizationService
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.transform import handler
from backend.domain.core.constants.permission_codes import RBAC_REVOKE_ROLE
from backend.domain.core.constants.rbac import RoleAction, SystemRole
from backend.domain.core.entities.base import TypeID
from backend.domain.core.exceptions.rbac import (
    RoleHierarchyViolationError as DomainRoleHierarchyViolationError,
)
from backend.domain.core.services.access_control import ensure_can_revoke_role


class RevokeRoleFromUserCommand(RevokeRoleFromUserDTO):
    actor_id: TypeID
    user_id: TypeID
    role: str


@handler(mode="write")
class RevokeRoleFromUserHandler(CommandHandler[RevokeRoleFromUserCommand, RoleAssignmentResultDTO]):
    uow: UnitOfWorkPort
    authorization_service: AuthorizationService

    async def _execute(self, cmd: RevokeRoleFromUserCommand, /) -> RoleAssignmentResultDTO:
        async with self.uow:
            context = await self.authorization_service.require_permission(
                user_id=cmd.actor_id,
                permission=RBAC_REVOKE_ROLE,
                rbac=self.uow.rbac,
            )
            try:
                role = SystemRole(cmd.role)
            except ValueError as e:
                raise ConflictError(f"Unknown role {cmd.role!r}") from e
            try:
                ensure_can_revoke_role(context.roles, role)
            except DomainRoleHierarchyViolationError as exc:
                raise RoleHierarchyViolationError(
                    action=RoleAction.REVOKE,
                    target_role=role,
                ) from exc
            try:
                await self.uow.users.get_one(user_id=cmd.user_id)
            except LookupError as exc:
                raise ResourceNotFoundError("User", str(cmd.user_id)) from exc
            roles = await self.uow.rbac.list_user_roles(user_id=cmd.user_id)
            if role not in roles:
                raise ConflictError(f"Role {role.value!r} is not assigned to user {cmd.user_id!r}")
            try:
                await self.uow.rbac.revoke_role_from_user(user_id=cmd.user_id, role=role)
            except LookupError as exc:
                raise ConflictError(f"Role {role.value!r} is not provisioned") from exc
            await self.uow.commit()

        return RoleAssignmentResultDTO(user_id=cmd.user_id, role=role.value)
