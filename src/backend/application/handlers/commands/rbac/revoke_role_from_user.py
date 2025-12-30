from __future__ import annotations

from backend.application.common.dtos.rbac import RevokeRoleFromUserDTO, RoleAssignmentResultDTO
from backend.application.common.exceptions.application import (
    ConflictError,
    ResourceNotFoundError,
    RoleHierarchyViolationError,
)
from backend.application.common.exceptions.db import ConstraintViolationError
from backend.application.common.exceptions.infra_mapper import map_infra_error_to_application
from backend.application.common.interfaces.persistence.uow import UnitOfWorkPort
from backend.application.common.services.authorization import AuthorizationService
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.transform import handler
from backend.domain.core.constants.permission_codes import RBAC_REVOKE_ROLE
from backend.domain.core.constants.rbac import RoleAction, SystemRole
from backend.domain.core.entities.base import TypeID
from backend.domain.core.exceptions.rbac import (
    LastSuperAdminRemovalError as DomainLastSuperAdminRemovalError,
)
from backend.domain.core.exceptions.rbac import (
    RoleHierarchyViolationError as DomainRoleHierarchyViolationError,
)
from backend.domain.core.exceptions.rbac import (
    RoleNotAssignedError as DomainRoleNotAssignedError,
)
from backend.domain.core.exceptions.rbac import (
    RoleSelfModificationError as DomainRoleSelfModificationError,
)
from backend.domain.core.services.access_control import (
    ensure_can_revoke_role,
    ensure_not_last_super_admin,
    ensure_not_self_role_change,
)


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
                user = await self.uow.users.get_one(user_id=cmd.user_id)
            except LookupError as exc:
                raise ResourceNotFoundError("User", str(cmd.user_id)) from exc
            try:
                ensure_not_self_role_change(
                    actor_id=cmd.actor_id,
                    target_user_id=user.id,
                    action=RoleAction.REVOKE,
                )
            except DomainRoleSelfModificationError as exc:
                raise ConflictError("User cannot revoke roles from self") from exc
            try:
                if role == SystemRole.SUPER_ADMIN and user.has_role(role):
                    super_admin_count = await self.uow.rbac.count_users_with_role(
                        role=SystemRole.SUPER_ADMIN
                    )
                    ensure_not_last_super_admin(
                        target_user_id=user.id,
                        remaining_super_admins=super_admin_count - 1,
                    )
            except DomainLastSuperAdminRemovalError as exc:
                raise ConflictError("Cannot revoke last super_admin role") from exc
            try:
                user.revoke_role(role)
                await self.uow.users.replace_roles(user)
            except DomainRoleNotAssignedError as exc:
                raise ConflictError(
                    f"Role {role.value!r} is not assigned to user {cmd.user_id!r}"
                ) from exc
            except LookupError as exc:
                raise ConflictError(f"Role {role.value!r} is not provisioned") from exc
            try:
                await self.uow.commit()
            except ConstraintViolationError as exc:
                raise map_infra_error_to_application(exc) from exc

        return RoleAssignmentResultDTO(user_id=cmd.user_id, role=role.value)
