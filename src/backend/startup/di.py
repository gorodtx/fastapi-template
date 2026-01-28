from __future__ import annotations

import os
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum, auto
from typing import TYPE_CHECKING, Protocol
from urllib.parse import urlparse

from dishka import AsyncContainer, Provider, Scope, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from starlette.requests import Request

from backend.application.common.dtos.auth import SuccessDTO, TokenPairDTO
from backend.application.common.dtos.rbac import UserRolesResponseDTO
from backend.application.common.dtos.users import UserResponseDTO
from backend.application.common.interfaces.auth.ports import (
    Authenticator,
    JwtIssuer,
    JwtVerifier,
    RefreshStore,
)
from backend.application.common.interfaces.ports.cache import StrCache
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.interfaces.ports.persistence.manager import (
    TransactionManager,
)
from backend.application.handlers.base import CommandHandler, QueryHandler
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
from backend.application.handlers.queries.rbac.get_user_roles import (
    GetUserRolesHandler,
    GetUserRolesQuery,
)
from backend.application.handlers.queries.users.get_user import (
    GetUserHandler,
    GetUserQuery,
)
from backend.domain.ports.security.password_hasher import PasswordHasherPort
from backend.infrastructure.lock.redis_lock import RedisSharedLock
from backend.infrastructure.persistence.cache.redis import RedisCache
from backend.infrastructure.persistence.manager import TransactionManagerImpl
from backend.infrastructure.persistence.persistence_gateway import (
    PersistenceGatewayImpl,
)
from backend.infrastructure.persistence.sqlalchemy.session_db import (
    create_engine,
    create_session_factory,
)
from backend.infrastructure.security.auth.authenticator import (
    AuthenticatorImpl,
)
from backend.infrastructure.security.auth.jwt import JwtConfig, JwtImpl
from backend.infrastructure.security.auth.refresh_store import RefreshStoreImpl
from backend.infrastructure.security.password_hasher import (
    Argon2PasswordHasher,
)


class _EventRegistrar(Protocol):
    def add_event_handler(
        self: _EventRegistrar,
        event_type: str,
        func: Callable[[], Awaitable[None] | None],
    ) -> None: ...


class _ProvideDecorator(Protocol):
    def __call__(self: _ProvideDecorator, func: object) -> object: ...


if TYPE_CHECKING:

    def provide(
        *,
        scope: Scope | None = None,
        provides: object | None = None,
        cache: bool = True,
        recursive: bool = False,
        override: bool = False,
    ) -> _ProvideDecorator: ...
else:
    from dishka import provide


class EnvKey(str, Enum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[object]
    ) -> str:
        del start, count, last_values
        return name

    DATABASE_URL = auto()
    REDIS_URL = auto()
    JWT_ISSUER = auto()
    JWT_AUDIENCE = auto()
    JWT_ALG = auto()
    JWT_SECRET = auto()
    JWT_ACCESS_TTL_S = auto()
    JWT_REFRESH_TTL_S = auto()


def _read_env(key: EnvKey) -> str | None:
    value = os.environ.get(key.value)
    if value is None or not value.strip():
        return None
    return value


def _require_env(key: EnvKey) -> str:
    value = _read_env(key)
    if value is None:
        raise RuntimeError(
            f"Missing required environment variable: {key.value}"
        )
    return value


def _require_env_int(key: EnvKey) -> int:
    raw = _require_env(key)
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid integer for {key.value}: {raw}") from exc


def _build_jwt_config() -> JwtConfig:
    return JwtConfig(
        issuer=_require_env(EnvKey.JWT_ISSUER),
        audience=_require_env(EnvKey.JWT_AUDIENCE),
        alg=_require_env(EnvKey.JWT_ALG),
        access_ttl=timedelta(
            seconds=_require_env_int(EnvKey.JWT_ACCESS_TTL_S)
        ),
        refresh_ttl=timedelta(
            seconds=_require_env_int(EnvKey.JWT_REFRESH_TTL_S)
        ),
        secret=_require_env(EnvKey.JWT_SECRET),
    )


def _build_redis_client(redis_url: str | None) -> Redis:
    if redis_url is None:
        return Redis()
    parsed = urlparse(redis_url)
    if parsed.scheme not in {"redis", "rediss"}:
        raise RuntimeError(f"Unsupported Redis URL scheme: {parsed.scheme}")
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    db = 0
    if parsed.path and parsed.path != "/":
        try:
            db = int(parsed.path.lstrip("/"))
        except ValueError as exc:
            raise RuntimeError(
                f"Invalid Redis database in URL: {parsed.path}"
            ) from exc
    return Redis(
        host=host,
        port=port,
        username=parsed.username,
        password=parsed.password,
        db=db,
        ssl=parsed.scheme == "rediss",
    )


@dataclass(slots=True)
class ApiHandlers:
    create_user: CommandHandler[CreateUserCommand, UserResponseDTO]
    get_user: QueryHandler[GetUserQuery, UserResponseDTO]
    get_user_roles: QueryHandler[GetUserRolesQuery, UserRolesResponseDTO]
    login_user: CommandHandler[LoginUserCommand, TokenPairDTO]
    logout_user: CommandHandler[LogoutUserCommand, SuccessDTO]
    refresh_user: CommandHandler[RefreshUserCommand, TokenPairDTO]


@dataclass(slots=True)
class AuthDependencies:
    auth_gateway: PersistenceGateway
    auth_jwt_verifier: JwtVerifier
    auth_authenticator: Authenticator
    auth_cache: StrCache


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def engine(self: AppProvider) -> AsyncEngine:
        return create_engine(_read_env(EnvKey.DATABASE_URL))

    @provide(scope=Scope.APP)
    def session_factory(
        self: AppProvider, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return create_session_factory(engine)

    @provide(scope=Scope.APP)
    async def redis_client(self: AppProvider) -> AsyncIterator[Redis]:
        client = _build_redis_client(_read_env(EnvKey.REDIS_URL))
        try:
            yield client
        finally:
            await client.aclose()

    @provide(scope=Scope.APP)
    def auth_cache(self: AppProvider, client: Redis) -> StrCache:
        return RedisCache(client)

    @provide(scope=Scope.APP)
    def shared_lock(self: AppProvider, client: Redis) -> RedisSharedLock:
        return RedisSharedLock(client)

    @provide(scope=Scope.APP)
    def refresh_store(
        self: AppProvider, cache: StrCache, lock: RedisSharedLock
    ) -> RefreshStore:
        return RefreshStoreImpl(cache=cache, lock=lock)

    @provide(scope=Scope.APP)
    def password_hasher(self: AppProvider) -> PasswordHasherPort:
        return Argon2PasswordHasher()

    @provide(scope=Scope.APP)
    def jwt_config(self: AppProvider) -> JwtConfig:
        return _build_jwt_config()

    @provide(scope=Scope.APP)
    def jwt_impl(self: AppProvider, cfg: JwtConfig) -> JwtImpl:
        return JwtImpl(cfg)

    @provide(scope=Scope.APP)
    def jwt_verifier(self: AppProvider, impl: JwtImpl) -> JwtVerifier:
        return impl

    @provide(scope=Scope.APP)
    def jwt_issuer(self: AppProvider, impl: JwtImpl) -> JwtIssuer:
        return impl


class RequestProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def session(
        self: RequestProvider,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def transaction_manager(
        self: RequestProvider, session: AsyncSession
    ) -> TransactionManager:
        return TransactionManagerImpl(session)

    @provide(scope=Scope.REQUEST)
    def persistence_gateway(
        self: RequestProvider, manager: TransactionManager
    ) -> PersistenceGateway:
        return PersistenceGatewayImpl(manager)

    @provide(scope=Scope.REQUEST)
    def authenticator(
        self: RequestProvider, gateway: PersistenceGateway
    ) -> Authenticator:
        return AuthenticatorImpl(users=gateway.users, rbac=gateway.rbac)

    @provide(scope=Scope.REQUEST)
    def create_user_handler(
        self: RequestProvider,
        gateway: PersistenceGateway,
        password_hasher: PasswordHasherPort,
    ) -> CreateUserHandler:
        return CreateUserHandler(
            gateway=gateway, password_hasher=password_hasher
        )

    @provide(scope=Scope.REQUEST)
    def get_user_handler(
        self: RequestProvider, gateway: PersistenceGateway
    ) -> GetUserHandler:
        return GetUserHandler(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def get_user_roles_handler(
        self: RequestProvider, gateway: PersistenceGateway
    ) -> GetUserRolesHandler:
        return GetUserRolesHandler(gateway=gateway)

    @provide(scope=Scope.REQUEST)
    def login_user_handler(
        self: RequestProvider,
        gateway: PersistenceGateway,
        password_hasher: PasswordHasherPort,
        jwt_issuer: JwtIssuer,
        refresh_store: RefreshStore,
    ) -> LoginUserHandler:
        return LoginUserHandler(
            gateway=gateway,
            password_hasher=password_hasher,
            jwt_issuer=jwt_issuer,
            refresh_store=refresh_store,
        )

    @provide(scope=Scope.REQUEST)
    def logout_user_handler(
        self: RequestProvider,
        jwt_verifier: JwtVerifier,
        refresh_store: RefreshStore,
    ) -> LogoutUserHandler:
        return LogoutUserHandler(
            jwt_verifier=jwt_verifier, refresh_store=refresh_store
        )

    @provide(scope=Scope.REQUEST)
    def refresh_user_handler(
        self: RequestProvider,
        jwt_verifier: JwtVerifier,
        jwt_issuer: JwtIssuer,
        refresh_store: RefreshStore,
    ) -> RefreshUserHandler:
        return RefreshUserHandler(
            jwt_verifier=jwt_verifier,
            jwt_issuer=jwt_issuer,
            refresh_store=refresh_store,
        )

    @provide(scope=Scope.REQUEST)
    def api_handlers(
        self: RequestProvider,
        create_user: CreateUserHandler,
        get_user: GetUserHandler,
        get_user_roles: GetUserRolesHandler,
        login_user: LoginUserHandler,
        logout_user: LogoutUserHandler,
        refresh_user: RefreshUserHandler,
    ) -> ApiHandlers:
        return ApiHandlers(
            create_user=create_user,
            get_user=get_user,
            get_user_roles=get_user_roles,
            login_user=login_user,
            logout_user=logout_user,
            refresh_user=refresh_user,
        )

    @provide(scope=Scope.REQUEST)
    def auth_dependencies(
        self: RequestProvider,
        gateway: PersistenceGateway,
        verifier: JwtVerifier,
        authenticator: Authenticator,
        cache: StrCache,
    ) -> AuthDependencies:
        return AuthDependencies(
            auth_gateway=gateway,
            auth_jwt_verifier=verifier,
            auth_authenticator=authenticator,
            auth_cache=cache,
        )


def build_container() -> AsyncContainer:
    return make_async_container(AppProvider(), RequestProvider())


def setup_di(app: FastAPI) -> None:
    container = build_container()
    setup_dishka(container, app)

    async def _close_container() -> None:
        await container.close()

    _register_shutdown(app, _close_container)


def _register_shutdown(
    registrar: _EventRegistrar,
    func: Callable[[], Awaitable[None] | None],
) -> None:
    registrar.add_event_handler("shutdown", func)


def _get_container(request: Request) -> AsyncContainer:
    try:
        raw: object | None = request.state.dishka_container
    except AttributeError:
        raw = None
    if not isinstance(raw, AsyncContainer):
        raise RuntimeError(
            "Dishka container is not configured on request state"
        )
    return raw


async def get_handlers(request: Request) -> ApiHandlers:
    container = _get_container(request)
    return await container.get(ApiHandlers)


async def get_auth_deps(request: Request) -> AuthDependencies:
    container = _get_container(request)
    return await container.get(AuthDependencies)
