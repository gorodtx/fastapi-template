from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Self
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
from backend.application.common.tools.refresh_tokens import (
    RefreshTokenService,
)
from backend.domain.core.types.rbac import RoleCode
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
from backend.presentation.settings import Settings


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
    def __init__(self: Self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    def settings(self: Self) -> Settings:
        return self._settings

    @provide(scope=Scope.APP)
    def default_registration_role(self: Self) -> RoleCode:
        return self._settings.default_registration_role_code

    @provide(scope=Scope.APP)
    def engine(self: Self) -> AsyncEngine:
        return create_engine(self._settings.database_url)

    @provide(scope=Scope.APP)
    def session_factory(
        self: Self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return create_session_factory(engine)

    @provide(scope=Scope.APP)
    async def redis_client(self: Self) -> AsyncIterator[Redis]:
        client = _build_redis_client(self._settings.redis_url)
        try:
            yield client
        finally:
            await client.aclose()

    @provide(scope=Scope.APP)
    def auth_cache(self: Self, client: Redis) -> StrCache:
        return RedisCache(client)

    @provide(scope=Scope.APP)
    def shared_lock(self: Self, client: Redis) -> RedisSharedLock:
        return RedisSharedLock(client=client)

    @provide(scope=Scope.APP)
    def refresh_store(self: Self, cache: StrCache) -> RefreshStore:
        return RefreshStoreImpl(cache=cache)

    @provide(scope=Scope.APP)
    def refresh_tokens(
        self: Self,
        store: RefreshStore,
        lock: RedisSharedLock,
        cfg: JwtConfig,
    ) -> RefreshTokenService:
        ttl_s = int(cfg.refresh_ttl.total_seconds())
        return RefreshTokenService(store=store, lock=lock, ttl_s=ttl_s)

    @provide(scope=Scope.APP)
    def password_hasher(self: Self) -> PasswordHasherPort:
        return Argon2PasswordHasher()

    @provide(scope=Scope.APP)
    def jwt_config(self: Self) -> JwtConfig:
        return JwtConfig(
            issuer=self._settings.jwt_issuer,
            audience=self._settings.jwt_audience,
            alg=self._settings.jwt_alg,
            access_ttl=timedelta(seconds=self._settings.jwt_access_ttl_s),
            refresh_ttl=timedelta(seconds=self._settings.jwt_refresh_ttl_s),
            secret=self._settings.jwt_secret,
        )

    @provide(scope=Scope.APP)
    def jwt_impl(self: Self, cfg: JwtConfig) -> JwtImpl:
        return JwtImpl(cfg)

    @provide(scope=Scope.APP)
    def jwt_verifier(self: Self, impl: JwtImpl) -> JwtVerifier:
        return impl

    @provide(scope=Scope.APP)
    def jwt_issuer(self: Self, impl: JwtImpl) -> JwtIssuer:
        return impl

    @provide(scope=Scope.APP)
    def auth_cache_invalidator(
        self: Self, cache: StrCache
    ) -> AuthCacheInvalidator:
        return AuthCacheInvalidator(cache=cache)
