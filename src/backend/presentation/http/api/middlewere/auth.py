from __future__ import annotations

import json
from collections.abc import Callable, Coroutine, Mapping
from enum import Enum
from typing import Final, ParamSpec, TypeGuard, TypeVar
from uuid import UUID

import msgspec
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.application.common.exceptions.application import (
    AuthorizationError,
    UnauthenticatedError,
)
from backend.application.common.interfaces.auth.context import Context
from backend.application.common.interfaces.auth.ports import Authenticator, JwtVerifier
from backend.application.common.interfaces.auth.types import (
    AuthUser,
    Permission,
    PermissionSpec,
    UserId,
)
from backend.application.common.interfaces.cache import StrCache
from backend.domain.core.constants.rbac import SystemRole
from backend.startup.di import get_auth_deps

_AUTH_REQUIRED_ATTR: Final[str] = "__auth_required__"
_AUTH_OPTIONAL_ATTR: Final[str] = "__auth_optional__"
_REQUIRED_PERMS_ATTR: Final[str] = "__required_permissions__"

_P = ParamSpec("_P")
_R = TypeVar("_R")


class Source(Enum):
    QUERY = "QUERY"
    JSON = "JSON"


def get_ctx(request: Request) -> Context:
    try:
        ctx: object | None = request.state.ctx
    except AttributeError:
        ctx = None
    if not isinstance(ctx, Context):
        raise RuntimeError("Context is not initialized. Did you add AuthContextMiddleware?")
    return ctx


def require_auth() -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    def deco(fn: Callable[_P, _R]) -> Callable[_P, _R]:
        fn.__dict__[_AUTH_REQUIRED_ATTR] = True
        return fn

    return deco


def auth_optional() -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    def deco(fn: Callable[_P, _R]) -> Callable[_P, _R]:
        fn.__dict__[_AUTH_OPTIONAL_ATTR] = True
        return fn

    return deco


def requires_permissions(
    *specs: PermissionSpec,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    def deco(fn: Callable[_P, _R]) -> Callable[_P, _R]:
        fn.__dict__[_REQUIRED_PERMS_ATTR] = specs
        return fn

    return deco


def _is_object_tuple(value: object) -> TypeGuard[tuple[object, ...]]:
    return isinstance(value, tuple)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _is_object_mapping(value: object) -> TypeGuard[Mapping[object, object]]:
    return isinstance(value, Mapping)


def _is_permission_spec_tuple(value: object) -> TypeGuard[tuple[PermissionSpec, ...]]:
    if not _is_object_tuple(value):
        return False
    return all(isinstance(item, PermissionSpec) for item in value)


def _to_str_key_dict(value: object) -> dict[str, object] | None:
    if not _is_object_mapping(value):
        return None
    return {str(key): item for key, item in value.items()}


def _to_str_frozenset_from_list(value: object) -> frozenset[str]:
    if not _is_object_list(value):
        return frozenset()
    return frozenset(str(item) for item in value)


def _required_permissions(value: object) -> tuple[PermissionSpec, ...]:
    if _is_permission_spec_tuple(value):
        return value
    if not _is_object_tuple(value):
        return ()
    sanitized: list[PermissionSpec] = []
    for item in value:
        if isinstance(item, PermissionSpec):
            sanitized.append(item)
    return tuple(sanitized)


class AuthContextMiddleware:
    __slots__ = ("_max_body_bytes", "_user_cache_ttl_cap_s", "app")

    def __init__(
        self, app: ASGIApp, *, max_body_bytes: int = 256 * 1024, user_cache_ttl_cap_s: int = 300
    ) -> None:
        self.app = app
        self._max_body_bytes = max_body_bytes
        self._user_cache_ttl_cap_s = user_cache_ttl_cap_s

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        deps = await get_auth_deps(request)

        ctx = Context(authenticator=deps.auth_authenticator, user=None)
        ctx.request_id = request.headers.get("x-request-id") or ""
        ctx.request_method = request.method
        ctx.request_path = request.url.path
        ctx.request_url = str(request.url)
        ctx.request_path_params = dict(request.path_params)
        ctx.request_query_params = dict(request.query_params)
        ctx.collect_keys(ctx.request_query_params)

        content_type = request.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            body = await request.body()
            if 0 < len(body) <= self._max_body_bytes:
                try:
                    parsed = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError:
                    parsed = None
                ctx.request_json_params = parsed
                ctx.collect_keys(parsed)

        auth_header = request.headers.get("authorization")
        if auth_header:
            await self._authenticate_into_context(
                ctx=ctx,
                auth_header=auth_header,
                verifier=deps.auth_jwt_verifier,
                authenticator=deps.auth_authenticator,
                cache=deps.auth_cache,
            )

        request.state.ctx = ctx
        await self.app(scope, request.receive, send)

    async def _authenticate_into_context(
        self,
        *,
        ctx: Context,
        auth_header: str,
        verifier: JwtVerifier,
        authenticator: Authenticator,
        cache: StrCache,
    ) -> None:
        token_str = auth_header.removeprefix("Bearer ").strip()
        user_id = verifier.verify_access(token_str).unwrap_or_raise(
            UnauthenticatedError("Invalid access token")
        )

        cache_key = f"auth:user:{user_id}"
        cached = await cache.get(cache_key)
        if cached is not None:
            cached_user = _decode_cached_user(cached)
            if cached_user is not None:
                ctx.set_user(cached_user)
                return

        auth_user = await authenticator.authenticate(user_id)
        if auth_user is None or not auth_user.is_active:
            raise UnauthenticatedError("User not found or inactive")

        ctx.set_user(auth_user)
        await cache.set(cache_key, _encode_cached_user(auth_user), ttl_s=self._user_cache_ttl_cap_s)


class AuthzRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[object, object, Response]]:
        original = super().get_route_handler()
        endpoint = self.endpoint
        try:
            endpoint_dict = dict(endpoint.__dict__)
        except AttributeError:
            endpoint_dict = {}
        required = _required_permissions(endpoint_dict.get(_REQUIRED_PERMS_ATTR))
        is_auth_required = bool(endpoint_dict.get(_AUTH_REQUIRED_ATTR, False))
        is_optional = bool(endpoint_dict.get(_AUTH_OPTIONAL_ATTR, False))

        async def custom_route_handler(request: Request) -> Response:
            ctx = get_ctx(request)
            if not required and not is_auth_required:
                return await original(request)
            if is_optional and ctx.user is None:
                return await original(request)
            if ctx.user is None:
                raise UnauthenticatedError("Authentication required")
            if not required:
                return await original(request)

            deps = await get_auth_deps(request)
            await _enforce_permissions(
                ctx=ctx,
                authenticator=deps.auth_authenticator,
                cache=deps.auth_cache,
                required=required,
            )
            return await original(request)

        return custom_route_handler


async def _enforce_permissions(
    *,
    ctx: Context,
    authenticator: Authenticator,
    cache: StrCache,
    required: tuple[PermissionSpec, ...],
) -> None:
    user = ctx.user
    if user is None:
        raise UnauthenticatedError("Authentication required")
    if user.is_superuser:
        return

    json_dict = _to_str_key_dict(ctx.request_json_params)
    if json_dict is None:
        json_keys: frozenset[str] = frozenset()
    else:
        json_keys = frozenset(json_dict)

    requested_fields: dict[Source, frozenset[str]] = {
        Source.QUERY: frozenset(ctx.request_query_params.keys()),
        Source.JSON: json_keys,
    }

    for spec in required:
        merged = PermissionSpec(
            code=spec.code,
            request_keys=ctx.request_keys() | spec.request_keys,
            deny_fields=spec.deny_fields,
            allow_all_fields=spec.allow_all_fields,
        )
        perm_key = merged.code.value
        cache_key = f"auth:perm:{user.id}:{perm_key}"
        cached = await cache.get(cache_key)
        if cached is None:
            perm = await authenticator.get_permission_for(user.id, merged)
            await cache.set(cache_key, _encode_permission(perm), ttl_s=30)
        else:
            perm = _decode_permission(cached)
        if not perm.allowed:
            raise AuthorizationError(f"Access denied by policy for {perm_key}")
        if not perm.allow_all_fields:
            for src, req_keys in requested_fields.items():
                if not req_keys:
                    continue
                denied = perm.deny_fields & req_keys
                if denied:
                    raise AuthorizationError(f"Denied fields in {src.name}: {sorted(denied)}")


def _encode_cached_user(user: AuthUser) -> str:
    payload = {
        "id": str(user.id),
        "roles": [role.value for role in user.roles],
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
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
    is_superuser = data.get("is_superuser", False)
    email = data.get("email")
    if (
        not isinstance(user_id, str)
        or not _is_object_list(roles)
        or not isinstance(is_active, bool)
    ):
        return None
    try:
        uid = UserId(UUID(user_id))
    except ValueError:
        return None
    role_set: set[SystemRole] = set()
    for raw_role in roles:
        role = _safe_role(raw_role)
        if role is not None:
            role_set.add(role)
    return AuthUser(
        id=uid,
        roles=frozenset(role_set),
        is_active=is_active,
        is_superuser=bool(is_superuser),
        email=email if isinstance(email, str) else None,
    )


def _safe_role(raw: object) -> SystemRole | None:
    if not isinstance(raw, str):
        return None
    try:
        return SystemRole(raw)
    except ValueError:
        return None


def _encode_permission(perm: Permission) -> str:
    payload = {
        "allowed": perm.allowed,
        "deny_fields": list(perm.deny_fields),
        "allow_all_fields": perm.allow_all_fields,
    }
    return msgspec.json.encode(payload).decode("utf-8")


def _decode_permission(raw: str) -> Permission:
    raw_data = msgspec.json.decode(raw.encode("utf-8"))
    data = _to_str_key_dict(raw_data)
    if data is not None:
        allowed = bool(data.get("allowed", False))
        deny_fields = _to_str_frozenset_from_list(data.get("deny_fields", []))
        allow_all_fields = bool(data.get("allow_all_fields", True))
        return Permission(
            allowed=allowed, deny_fields=deny_fields, allow_all_fields=allow_all_fields
        )
    return Permission(allowed=False)
