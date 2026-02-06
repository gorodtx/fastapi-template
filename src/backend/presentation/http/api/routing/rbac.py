from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from uuid_utils.compat import UUID

from backend.application.common.interfaces.auth.types import AuthUser
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.tools.auth_cache import AuthCacheInvalidator
from backend.application.common.tools.permission_guard import PermissionGuard
from backend.application.handlers.commands.rbac.assign_role_to_user import (
    AssignRoleToUserCommand,
    AssignRoleToUserHandler,
)
from backend.application.handlers.commands.rbac.revoke_role_from_user import (
    RevokeRoleFromUserCommand,
    RevokeRoleFromUserHandler,
)
from backend.application.handlers.queries.rbac.get_user_roles import (
    GetUserRolesHandler,
    GetUserRolesQuery,
)
from backend.domain.core.constants.permission_codes import (
    RBAC_ASSIGN_ROLE,
    RBAC_READ_ROLES,
    RBAC_REVOKE_ROLE,
)
from backend.presentation.http.api.schemas.rbac import (
    RoleChangeRequest,
    UserRolesResponse,
)

router: APIRouter = APIRouter(route_class=DishkaRoute)


@router.get("/rbac/users/{user_id}/roles", response_model=UserRolesResponse)
async def get_user_roles(
    user_id: UUID,
    gateway: FromDishka[PersistenceGateway],
    current_user: FromDishka[AuthUser],
    permission_guard: FromDishka[PermissionGuard],
) -> UserRolesResponse:
    await permission_guard.require(current_user, RBAC_READ_ROLES)
    handler = GetUserRolesHandler(gateway=gateway)
    result = await handler(GetUserRolesQuery(user_id=user_id))
    dto = result.unwrap()

    return UserRolesResponse.from_dto(dto)


@router.post("/rbac/users/{user_id}/roles", response_model=UserRolesResponse)
async def assign_role_to_user(
    user_id: UUID,
    payload: RoleChangeRequest,
    gateway: FromDishka[PersistenceGateway],
    cache_invalidator: FromDishka[AuthCacheInvalidator],
    current_user: FromDishka[AuthUser],
    permission_guard: FromDishka[PermissionGuard],
) -> UserRolesResponse:
    await permission_guard.require(current_user, RBAC_ASSIGN_ROLE)
    handler = AssignRoleToUserHandler(
        gateway=gateway,
        cache_invalidator=cache_invalidator,
    )
    cmd = AssignRoleToUserCommand(
        user_id=user_id,
        role=payload.role,
        actor_id=current_user.id,
        actor_roles=current_user.roles,
    )
    result = await handler(cmd)
    dto = result.unwrap()

    return UserRolesResponse.from_dto(dto)


@router.delete(
    "/rbac/users/{user_id}/roles/{role}",
    response_model=UserRolesResponse,
)
async def revoke_role_from_user(
    user_id: UUID,
    role: str,
    gateway: FromDishka[PersistenceGateway],
    cache_invalidator: FromDishka[AuthCacheInvalidator],
    current_user: FromDishka[AuthUser],
    permission_guard: FromDishka[PermissionGuard],
) -> UserRolesResponse:
    await permission_guard.require(current_user, RBAC_REVOKE_ROLE)
    handler = RevokeRoleFromUserHandler(
        gateway=gateway,
        cache_invalidator=cache_invalidator,
    )
    cmd = RevokeRoleFromUserCommand(
        user_id=user_id,
        role=role,
        actor_id=current_user.id,
        actor_roles=current_user.roles,
    )
    result = await handler(cmd)
    dto = result.unwrap()

    return UserRolesResponse.from_dto(dto)
