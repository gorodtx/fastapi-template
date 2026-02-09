from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from backend.application.common.exceptions.error_mappers.auth import (
    map_refresh_replay,
)
from backend.application.common.interfaces.auth.ports import (
    JwtIssuer,
    JwtVerifier,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.tools.refresh_tokens import (
    RefreshTokenService,
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
from backend.application.handlers.commands.users.create import (
    CreateUserCommand,
    CreateUserHandler,
)
from backend.domain.ports.security.password_hasher import PasswordHasherPort
from backend.presentation.http.api.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    SuccessResponse,
    TokenPairResponse,
)

router: APIRouter = APIRouter(route_class=DishkaRoute)


@router.post("/auth/register", response_model=TokenPairResponse)
async def register_user(
    payload: RegisterRequest,
    gateway: FromDishka[PersistenceGateway],
    password_hasher: FromDishka[PasswordHasherPort],
    jwt_issuer: FromDishka[JwtIssuer],
    refresh_tokens: FromDishka[RefreshTokenService],
) -> TokenPairResponse:
    create_handler = CreateUserHandler(
        gateway=gateway,
        password_hasher=password_hasher,
    )
    create_cmd = CreateUserCommand(
        email=payload.email,
        login=payload.login,
        username=payload.username,
        raw_password=payload.raw_password,
    )
    create_result = await create_handler(create_cmd)
    user = create_result.unwrap()

    access_token = jwt_issuer.issue_access(user_id=user.id)
    refresh_token, refresh_jti = jwt_issuer.issue_refresh(
        user_id=user.id,
        fingerprint=payload.fingerprint,
    )

    try:
        await refresh_tokens.rotate(
            user_id=user.id,
            fingerprint=payload.fingerprint,
            old_jti="",
            new_jti=refresh_jti,
        )
    except Exception as exc:
        raise map_refresh_replay()(exc) from exc

    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/auth/login", response_model=TokenPairResponse)
async def login_user(
    payload: LoginRequest,
    gateway: FromDishka[PersistenceGateway],
    password_hasher: FromDishka[PasswordHasherPort],
    jwt_issuer: FromDishka[JwtIssuer],
    refresh_tokens: FromDishka[RefreshTokenService],
) -> TokenPairResponse:
    handler = LoginUserHandler(
        gateway=gateway,
        password_hasher=password_hasher,
        jwt_issuer=jwt_issuer,
        refresh_tokens=refresh_tokens,
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
    refresh_tokens: FromDishka[RefreshTokenService],
) -> SuccessResponse:
    handler = LogoutUserHandler(
        jwt_verifier=jwt_verifier,
        refresh_tokens=refresh_tokens,
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
    refresh_tokens: FromDishka[RefreshTokenService],
) -> TokenPairResponse:
    handler = RefreshUserHandler(
        jwt_verifier=jwt_verifier,
        jwt_issuer=jwt_issuer,
        refresh_tokens=refresh_tokens,
    )
    cmd = RefreshUserCommand(
        refresh_token=payload.refresh_token, fingerprint=payload.fingerprint
    )
    result = await handler(cmd)
    dto = result.unwrap()

    return TokenPairResponse.from_dto(dto)
