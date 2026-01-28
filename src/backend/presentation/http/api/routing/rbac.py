from __future__ import annotations

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter
from uuid_utils.compat import UUID

from backend.application.common.interfaces.auth.types import AuthUser
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.tools.permission_guard import PermissionGuard
from backend.application.handlers.queries.rbac.get_user_roles import (
    GetUserRolesHandler,
    GetUserRolesQuery,
)
from backend.domain.core.constants.permission_codes import RBAC_READ_ROLES
from backend.presentation.http.api.schemas.rbac import UserRolesResponse

router: APIRouter = APIRouter()


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
