from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import timedelta
from enum import Enum, auto
from urllib.parse import urlparse

from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from backend.application.common.interfaces.auth.ports import (
    JwtIssuer,
    JwtVerifier,
    RefreshStore,
)
from backend.application.common.interfaces.ports.cache import StrCache
from backend.application.common.tools.auth_cache import AuthCacheInvalidator
from backend.domain.ports.security.password_hasher import PasswordHasherPort
from backend.infrastructure.lock.redis_lock import RedisSharedLock
from backend.infrastructure.persistence.cache.redis import RedisCache
from backend.infrastructure.persistence.sqlalchemy.session_db import (
    create_engine,
    create_session_factory,
)
from backend.infrastructure.security.auth.jwt import JwtConfig, JwtImpl
from backend.infrastructure.security.auth.refresh_store import RefreshStoreImpl
from backend.infrastructure.security.password_hasher import (
    Argon2PasswordHasher,
)


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

    @provide(scope=Scope.APP)
    def auth_cache_invalidator(
        self: AppProvider, cache: StrCache
    ) -> AuthCacheInvalidator:
        return AuthCacheInvalidator(cache=cache)
