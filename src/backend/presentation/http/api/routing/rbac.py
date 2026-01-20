from __future__ import annotations

from fastapi import APIRouter
from uuid_utils.compat import UUID

from backend.application.common.interfaces.auth.types import PermissionSpec
from backend.application.handlers.queries.rbac.get_user_roles import GetUserRolesQuery
from backend.domain.core.constants.permission_codes import RBAC_READ_ROLES
from backend.presentation.http.api.dependencies import ApiHandlers
from backend.presentation.http.api.middlewere.auth import AuthzRoute, requires_permissions
from backend.presentation.http.api.schemas.rbac import UserRolesResponse
from dishka.integrations.fastapi import FromDishka, inject

router = APIRouter(route_class=AuthzRoute)


@router.get("/rbac/users/{user_id}/roles", response_model=UserRolesResponse)
@requires_permissions(PermissionSpec(code=RBAC_READ_ROLES))
@inject
async def get_user_roles(
    user_id: UUID,
    handlers: FromDishka[ApiHandlers],
) -> UserRolesResponse:
    result = await handlers.get_user_roles(GetUserRolesQuery(user_id=user_id))
    dto = result.unwrap()
    return UserRolesResponse(
        user_id=dto.user_id,
        roles=list(dto.roles),
        permissions=list(dto.permissions),
    )
