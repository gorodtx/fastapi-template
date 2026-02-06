from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import Self, TypeGuard

import msgspec
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
from backend.domain.core.constants.rbac import SystemRole
from backend.infrastructure.persistence.manager import TransactionManagerImpl
from backend.infrastructure.persistence.persistence_gateway import (
    PersistenceGatewayImpl,
)
from backend.infrastructure.security.auth.authenticator import (
    AuthenticatorImpl,
)

_AUTH_USER_CACHE_TTL_S: int = 300
_ROLLBACK_ONLY_SCOPE_KEY: str = "backend.rollback_only"


def _extract_bearer_token(request: Request) -> str:
    raw = request.headers.get("Authorization")
    if raw is None:
        raise UnauthenticatedError("Authorization token missing")
    prefix = "Bearer "
    if not raw.startswith(prefix):
        raise UnauthenticatedError("Invalid authorization header")
    token = raw[len(prefix) :].strip()
    if not token:
        raise UnauthenticatedError("Authorization token missing")
    return token


def _user_cache_key(user_id: UUID) -> str:
    return f"auth:user:{user_id}"


def _encode_cached_user(user: AuthUser) -> str:
    payload = {
        "id": str(user.id),
        "roles": [role.value for role in user.roles],
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_admin": user.is_admin,
        "email": user.email,
    }
    return msgspec.json.encode(payload).decode("utf-8")


def _decode_cached_user(raw: str) -> AuthUser | None:
    try:
        raw_data = msgspec.json.decode(raw.encode("utf-8"))
    except msgspec.DecodeError:
        return None
    data = _to_str_key_dict(raw_data)
    if data is None:
        return None
    user_id = data.get("id")
    roles = data.get("roles")
    is_active = data.get("is_active")
    email = data.get("email")
    if (
        not isinstance(user_id, str)
        or not _is_object_list(roles)
        or not isinstance(is_active, bool)
    ):
        return None
    try:
        uid = UUID(user_id)
    except ValueError:
        return None
    role_set: set[SystemRole] = set()
    for raw_role in roles:
        role = _safe_role(raw_role)
        if role is not None:
            role_set.add(role)
    is_superuser = SystemRole.SUPER_ADMIN in role_set
    is_admin = is_superuser or SystemRole.ADMIN in role_set
    return AuthUser(
        id=uid,
        roles=frozenset(role_set),
        is_active=is_active,
        is_superuser=is_superuser,
        is_admin=is_admin,
        email=email if isinstance(email, str) else None,
    )


def _safe_role(raw: object) -> SystemRole | None:
    if not isinstance(raw, str):
        return None
    try:
        return SystemRole(raw)
    except ValueError:
        return None


def _to_str_key_dict(value: object) -> dict[str, object] | None:
    if not _is_mapping(value):
        return None
    out: dict[str, object] = {}
    for key, item in value.items():
        out[str(key)] = item
    return out


def _is_mapping(value: object) -> TypeGuard[Mapping[object, object]]:
    return isinstance(value, Mapping)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


class RequestProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def session(
        self: Self,
        request: Request,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AsyncSession]:
        request.scope.pop(_ROLLBACK_ONLY_SCOPE_KEY, None)
        async with session_factory() as session:
            await session.begin()
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            else:
                if request.scope.get(_ROLLBACK_ONLY_SCOPE_KEY):
                    try:
                        await session.rollback()
                    except Exception:
                        return
                else:
                    try:
                        await session.commit()
                    except Exception:
                        await session.rollback()
                        raise

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
    def permission_guard(self: Self, cache: StrCache) -> PermissionGuard:
        return PermissionGuard(cache=cache)

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
                    raise UnauthenticatedError("User not found or inactive")
                return cached_user
        auth_user = await authenticator.authenticate(user_id)
        if auth_user is None or not auth_user.is_active:
            raise UnauthenticatedError("User not found or inactive")
        await cache.set(
            cache_key,
            _encode_cached_user(auth_user),
            ttl_s=_AUTH_USER_CACHE_TTL_S,
        )
        return auth_user
