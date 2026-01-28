from __future__ import annotations

from fastapi import APIRouter
from starlette.requests import Request

from backend.application.handlers.commands.auth.login import LoginUserCommand
from backend.application.handlers.commands.auth.logout import LogoutUserCommand
from backend.application.handlers.commands.auth.refresh import (
    RefreshUserCommand,
)
from backend.presentation.http.api.middlewere.auth import (
    AuthzRoute,
    auth_optional,
)
from backend.presentation.http.api.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SuccessResponse,
    TokenPairResponse,
)
from backend.startup.di import get_handlers

router: APIRouter = APIRouter(route_class=AuthzRoute)


@router.post("/auth/login", response_model=TokenPairResponse)
@auth_optional()
async def login_user(
    payload: LoginRequest,
    request: Request,
) -> TokenPairResponse:
    handlers = await get_handlers(request)
    cmd = LoginUserCommand(
        email=payload.email,
        raw_password=payload.raw_password,
        fingerprint=payload.fingerprint,
    )
    result = await handlers.login_user(cmd)
    dto = result.unwrap()
    return TokenPairResponse(
        access_token=dto.access_token,
        refresh_token=dto.refresh_token,
    )


@router.post("/auth/logout", response_model=SuccessResponse)
@auth_optional()
async def logout_user(
    payload: LogoutRequest,
    request: Request,
) -> SuccessResponse:
    handlers = await get_handlers(request)
    cmd = LogoutUserCommand(
        refresh_token=payload.refresh_token,
        fingerprint=payload.fingerprint,
    )
    result = await handlers.logout_user(cmd)
    dto = result.unwrap()
    return SuccessResponse(success=dto.success)


@router.post("/auth/refresh", response_model=TokenPairResponse)
@auth_optional()
async def refresh_user(
    payload: RefreshRequest, request: Request
) -> TokenPairResponse:
    handlers = await get_handlers(request)
    cmd = RefreshUserCommand(
        refresh_token=payload.refresh_token, fingerprint=payload.fingerprint
    )
    result = await handlers.refresh_user(cmd)
    dto = result.unwrap()

    return TokenPairResponse(
        access_token=dto.access_token, refresh_token=dto.refresh_token
    )
