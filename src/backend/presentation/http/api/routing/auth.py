from __future__ import annotations

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter

from backend.application.common.interfaces.auth.ports import (
    JwtIssuer,
    JwtVerifier,
    RefreshStore,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.handlers.commands.auth.login import (
    LoginUserCommand,
    LoginUserHandler,
)
from backend.application.handlers.commands.auth.logout import (
    LogoutUserCommand,
    LogoutUserHandler,
)
from backend.application.handlers.commands.auth.refresh import (
    RefreshUserCommand,
    RefreshUserHandler,
)
from backend.domain.ports.security.password_hasher import PasswordHasherPort
from backend.presentation.http.api.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SuccessResponse,
    TokenPairResponse,
)

router: APIRouter = APIRouter()


@router.post("/auth/login", response_model=TokenPairResponse)
async def login_user(
    payload: LoginRequest,
    gateway: FromDishka[PersistenceGateway],
    password_hasher: FromDishka[PasswordHasherPort],
    jwt_issuer: FromDishka[JwtIssuer],
    refresh_store: FromDishka[RefreshStore],
) -> TokenPairResponse:
    handler = LoginUserHandler(
        gateway=gateway,
        password_hasher=password_hasher,
        jwt_issuer=jwt_issuer,
        refresh_store=refresh_store,
    )
    cmd = LoginUserCommand(
        email=payload.email,
        raw_password=payload.raw_password,
        fingerprint=payload.fingerprint,
    )
    result = await handler(cmd)
    dto = result.unwrap()

    return TokenPairResponse.from_dto(dto)


@router.post("/auth/logout", response_model=SuccessResponse)
async def logout_user(
    payload: LogoutRequest,
    jwt_verifier: FromDishka[JwtVerifier],
    refresh_store: FromDishka[RefreshStore],
) -> SuccessResponse:
    handler = LogoutUserHandler(
        jwt_verifier=jwt_verifier,
        refresh_store=refresh_store,
    )
    cmd = LogoutUserCommand(
        refresh_token=payload.refresh_token,
        fingerprint=payload.fingerprint,
    )
    result = await handler(cmd)
    dto = result.unwrap()

    return SuccessResponse.from_dto(dto)


@router.post("/auth/refresh", response_model=TokenPairResponse)
async def refresh_user(
    payload: RefreshRequest,
    jwt_verifier: FromDishka[JwtVerifier],
    jwt_issuer: FromDishka[JwtIssuer],
    refresh_store: FromDishka[RefreshStore],
) -> TokenPairResponse:
    handler = RefreshUserHandler(
        jwt_verifier=jwt_verifier,
        jwt_issuer=jwt_issuer,
        refresh_store=refresh_store,
    )
    cmd = RefreshUserCommand(
        refresh_token=payload.refresh_token, fingerprint=payload.fingerprint
    )
    result = await handler(cmd)
    dto = result.unwrap()

    return TokenPairResponse.from_dto(dto)
