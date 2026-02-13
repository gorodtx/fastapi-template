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
from backend.presentation.http.api.post_commit import run_best_effort
from backend.presentation.http.api.schemas.rbac import (
    RoleChangeRequest,
    UserRolesResponse,
)
from backend.presentation.http.api.schemas.rbac_fields import RoleCodePath

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
    )
    cmd = AssignRoleToUserCommand(
        user_id=user_id,
        role=payload.role_code,
        actor_id=current_user.id,
        actor_roles=current_user.role_codes,
    )
    result = await handler(cmd)
    dto = result.unwrap()
    await run_best_effort(
        cache_invalidator.invalidate_user(user_id),
        effect="auth-cache invalidation after role assign",
    )

    return UserRolesResponse.from_dto(dto)


@router.delete(
    "/rbac/users/{user_id}/roles/{role_code}",
    response_model=UserRolesResponse,
)
async def revoke_role_from_user(
    user_id: UUID,
    role_code: RoleCodePath,
    gateway: FromDishka[PersistenceGateway],
    cache_invalidator: FromDishka[AuthCacheInvalidator],
    current_user: FromDishka[AuthUser],
    permission_guard: FromDishka[PermissionGuard],
) -> UserRolesResponse:
    await permission_guard.require(current_user, RBAC_REVOKE_ROLE)
    handler = RevokeRoleFromUserHandler(
        gateway=gateway,
    )
    cmd = RevokeRoleFromUserCommand(
        user_id=user_id,
        role=role_code,
        actor_id=current_user.id,
        actor_roles=current_user.role_codes,
    )
    result = await handler(cmd)
    dto = result.unwrap()
    await run_best_effort(
        cache_invalidator.invalidate_user(user_id),
        effect="auth-cache invalidation after role revoke",
    )

    return UserRolesResponse.from_dto(dto)
