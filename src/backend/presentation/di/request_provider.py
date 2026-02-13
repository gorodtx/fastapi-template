from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Self

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.requests import Request
from uuid_utils.compat import UUID

from backend.application.common.exceptions.application import (
    UnauthenticatedError,
)
from backend.application.common.interfaces.auth.ports import (
    Authenticator,
    JwtVerifier,
)
from backend.application.common.interfaces.auth.types import AuthUser
from backend.application.common.interfaces.ports.cache import StrCache
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.interfaces.ports.persistence.manager import (
    TransactionManager,
)
from backend.application.common.tools.permission_guard import PermissionGuard
from backend.infrastructure.persistence.manager import TransactionManagerImpl
from backend.infrastructure.persistence.persistence_gateway import (
    PersistenceGatewayImpl,
)
from backend.infrastructure.security.auth.authenticator import (
    AuthenticatorImpl,
)
from backend.infrastructure.security.auth.cache_codec import (
    decode_cached_user,
    encode_cached_user,
)

_AUTH_USER_CACHE_TTL_S: int = 300


def _extract_bearer_token(request: Request) -> str:
    raw = request.headers.get("Authorization")
    if raw is None:
        raise UnauthenticatedError("Authentication required")
    prefix = "Bearer "
    if not raw.startswith(prefix):
        raise UnauthenticatedError("Authentication required")
    token = raw[len(prefix) :].strip()
    if not token:
        raise UnauthenticatedError("Authentication required")
    return token


def _user_cache_key(user_id: UUID) -> str:
    return f"auth:user:{user_id}"


def _decode_cached_user(raw: str) -> AuthUser | None:
    return decode_cached_user(raw)


def _encode_cached_user(user: AuthUser) -> str:
    return encode_cached_user(user)


class RequestProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def session(
        self: Self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def transaction_manager(
        self: Self, session: AsyncSession
    ) -> TransactionManager:
        return TransactionManagerImpl(session)

    @provide(scope=Scope.REQUEST)
    def persistence_gateway(
        self: Self, manager: TransactionManager
    ) -> PersistenceGateway:
        return PersistenceGatewayImpl(manager)

    @provide(scope=Scope.REQUEST)
    def authenticator(
        self: Self, gateway: PersistenceGateway
    ) -> Authenticator:
        return AuthenticatorImpl(users=gateway.users, rbac=gateway.rbac)

    @provide(scope=Scope.REQUEST)
    def permission_guard(self: Self) -> PermissionGuard:
        return PermissionGuard()

    @provide(scope=Scope.REQUEST)
    async def current_user(
        self: Self,
        request: Request,
        jwt_verifier: JwtVerifier,
        authenticator: Authenticator,
        cache: StrCache,
    ) -> AuthUser:
        token = _extract_bearer_token(request)
        user_id = jwt_verifier.verify_access(token).unwrap_or_raise(
            UnauthenticatedError("Invalid access token")
        )
        cache_key = _user_cache_key(user_id)
        cached = await cache.get(cache_key)
        if cached is not None:
            cached_user = _decode_cached_user(cached)
            if cached_user is not None:
                if not cached_user.is_active:
                    raise UnauthenticatedError("Authentication required")
                return cached_user
        auth_user = await authenticator.authenticate(user_id)
        if auth_user is None or not auth_user.is_active:
            raise UnauthenticatedError("Authentication required")
        await cache.set(
            cache_key,
            _encode_cached_user(auth_user),
            ttl_s=_AUTH_USER_CACHE_TTL_S,
        )
        return auth_user
