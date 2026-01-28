from __future__ import annotations

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter

from backend.application.common.interfaces.auth.types import AuthUser
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.tools.permission_guard import PermissionGuard
from backend.application.handlers.commands.users.create import (
    CreateUserCommand,
    CreateUserHandler,
)
from backend.application.handlers.queries.users.get_user import (
    GetUserHandler,
    GetUserQuery,
)
from backend.domain.core.constants.permission_codes import USERS_CREATE
from backend.domain.ports.security.password_hasher import PasswordHasherPort
from backend.presentation.http.api.schemas.users import (
    UserCreateRequest,
    UserResponse,
)

router: APIRouter = APIRouter()


@router.post("/users", response_model=UserResponse)
async def create_user(
    payload: UserCreateRequest,
    gateway: FromDishka[PersistenceGateway],
    password_hasher: FromDishka[PasswordHasherPort],
    current_user: FromDishka[AuthUser],
    permission_guard: FromDishka[PermissionGuard],
) -> UserResponse:
    await permission_guard.require(current_user, USERS_CREATE)
    handler = CreateUserHandler(
        gateway=gateway,
        password_hasher=password_hasher,
    )
    cmd = CreateUserCommand(
        email=str(payload.email),
        login=payload.login,
        username=payload.username,
        raw_password=payload.raw_password,
    )
    result = await handler(cmd)
    dto = result.unwrap()

    return UserResponse.from_dto(dto)


@router.get("/users/me", response_model=UserResponse)
async def get_me(
    gateway: FromDishka[PersistenceGateway],
    current_user: FromDishka[AuthUser],
) -> UserResponse:
    handler = GetUserHandler(gateway=gateway)
    result = await handler(GetUserQuery(user_id=current_user.id))
    dto = result.unwrap()

    return UserResponse.from_dto(dto)
