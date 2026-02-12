from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import UUID

from backend.application.common.interfaces.auth.types import AuthUser
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.tools.auth_cache import AuthCacheInvalidator
from backend.application.common.tools.permission_guard import PermissionGuard
from backend.application.handlers.commands.users.create import (
    CreateUserCommand,
    CreateUserHandler,
)
from backend.application.handlers.commands.users.delete import (
    DeleteUserCommand,
    DeleteUserHandler,
)
from backend.application.handlers.commands.users.update import (
    UpdateUserCommand,
    UpdateUserHandler,
)
from backend.application.handlers.queries.users.get_user import (
    GetUserHandler,
    GetUserQuery,
)
from backend.domain.core.constants.permission_codes import (
    USERS_CREATE,
    USERS_DELETE,
    USERS_UPDATE,
)
from backend.domain.core.types.rbac import RoleCode
from backend.domain.ports.security.password_hasher import PasswordHasherPort
from backend.presentation.http.api.schemas.auth import SuccessResponse
from backend.presentation.http.api.schemas.users import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from backend.presentation.http.api.tx import run_write_in_tx

router: APIRouter = APIRouter(route_class=DishkaRoute)


@router.post("/users", response_model=UserResponse)
async def create_user(
    payload: UserCreateRequest,
    session: FromDishka[AsyncSession],
    gateway: FromDishka[PersistenceGateway],
    password_hasher: FromDishka[PasswordHasherPort],
    default_registration_role: FromDishka[RoleCode],
    current_user: FromDishka[AuthUser],
    permission_guard: FromDishka[PermissionGuard],
) -> UserResponse:
    await permission_guard.require(current_user, USERS_CREATE)
    handler = CreateUserHandler(
        gateway=gateway,
        password_hasher=password_hasher,
        default_registration_role=default_registration_role,
    )
    cmd = CreateUserCommand(
        email=str(payload.email),
        login=payload.login,
        username=payload.username,
        raw_password=payload.raw_password,
    )
    dto = await run_write_in_tx(session, handler(cmd))

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


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    session: FromDishka[AsyncSession],
    gateway: FromDishka[PersistenceGateway],
    password_hasher: FromDishka[PasswordHasherPort],
    cache_invalidator: FromDishka[AuthCacheInvalidator],
    current_user: FromDishka[AuthUser],
    permission_guard: FromDishka[PermissionGuard],
) -> UserResponse:
    await permission_guard.require(current_user, USERS_UPDATE)
    handler = UpdateUserHandler(
        gateway=gateway,
        password_hasher=password_hasher,
    )
    cmd = UpdateUserCommand(
        user_id=user_id,
        email=str(payload.email) if payload.email is not None else None,
        raw_password=payload.raw_password,
    )
    dto = await run_write_in_tx(session, handler(cmd))
    await cache_invalidator.invalidate_user(user_id)

    return UserResponse.from_dto(dto)


@router.delete("/users/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: UUID,
    session: FromDishka[AsyncSession],
    gateway: FromDishka[PersistenceGateway],
    cache_invalidator: FromDishka[AuthCacheInvalidator],
    current_user: FromDishka[AuthUser],
    permission_guard: FromDishka[PermissionGuard],
) -> SuccessResponse:
    await permission_guard.require(current_user, USERS_DELETE)
    handler = DeleteUserHandler(
        gateway=gateway,
    )
    cmd = DeleteUserCommand(user_id=user_id)
    dto = await run_write_in_tx(session, handler(cmd))
    await cache_invalidator.invalidate_user(user_id)

    return SuccessResponse.from_dto(dto)
