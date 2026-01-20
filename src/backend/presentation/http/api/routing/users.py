from __future__ import annotations

from fastapi import APIRouter, Depends
from uuid_utils.compat import UUID

from backend.application.common.dtos.users import UserResponseDTO
from backend.application.common.exceptions.application import UnauthenticatedError
from backend.application.common.interfaces.auth.context import Context
from backend.application.handlers.commands.users.create import CreateUserCommand
from backend.application.handlers.queries.users.get_user import GetUserQuery
from backend.presentation.http.api.dependencies import ApiHandlers
from backend.presentation.http.api.middlewere.auth import (
    AuthzRoute,
    auth_optional,
    get_ctx,
    require_auth,
)
from backend.presentation.http.api.schemas.users import UserCreateRequest, UserResponse
from dishka.integrations.fastapi import FromDishka, inject

router = APIRouter(route_class=AuthzRoute)


@router.post("/users", response_model=UserResponse)
@auth_optional()
@inject
async def create_user(
    payload: UserCreateRequest,
    handlers: FromDishka[ApiHandlers],
) -> UserResponse:
    cmd = CreateUserCommand(
        email=str(payload.email),
        login=payload.login,
        username=payload.username,
        raw_password=payload.raw_password,
    )
    result = await handlers.create_user(cmd)
    dto = result.unwrap()
    return _to_user_response(dto)


@router.get("/users/me", response_model=UserResponse)
@require_auth()
@inject
async def get_me(
    handlers: FromDishka[ApiHandlers],
    ctx: Context = Depends(get_ctx),
) -> UserResponse:
    user = ctx.user
    if user is None:
        raise UnauthenticatedError("Authentication required")
    user_id = UUID(str(user.id))
    result = await handlers.get_user(GetUserQuery(user_id=user_id))
    dto = result.unwrap()
    return _to_user_response(dto)


def _to_user_response(dto: UserResponseDTO) -> UserResponse:
    return UserResponse(
        id=dto.id,
        email=dto.email,
        login=dto.login,
        username=dto.username,
    )
