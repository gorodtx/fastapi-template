from __future__ import annotations

from fastapi import APIRouter
from starlette.requests import Request
from uuid_utils.compat import UUID

from backend.application.common.dtos.users import UserResponseDTO
from backend.application.common.exceptions.application import (
    UnauthenticatedError,
)
from backend.application.handlers.commands.users.create import (
    CreateUserCommand,
)
from backend.application.handlers.queries.users.get_user import GetUserQuery
from backend.presentation.http.api.middlewere.auth import (
    AuthzRoute,
    auth_optional,
    get_ctx,
    require_auth,
)
from backend.presentation.http.api.schemas.users import (
    UserCreateRequest,
    UserResponse,
)
from backend.startup.di import get_handlers

router: APIRouter = APIRouter(route_class=AuthzRoute)


@router.post("/users", response_model=UserResponse)
@auth_optional()
async def create_user(
    payload: UserCreateRequest,
    request: Request,
) -> UserResponse:
    handlers = await get_handlers(request)
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
async def get_me(
    request: Request,
) -> UserResponse:
    ctx = get_ctx(request)
    user = ctx.user
    if user is None:
        raise UnauthenticatedError("Authentication required")
    user_id = UUID(str(user.id))
    handlers = await get_handlers(request)
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
