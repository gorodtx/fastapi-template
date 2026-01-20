from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.application.common.exceptions.application import AppError
from backend.application.common.interfaces.auth.ports import Authenticator, JwtVerifier
from backend.application.common.interfaces.cache import StrCache
from backend.application.common.interfaces.infra.persistence.gateway import PersistenceGateway
from backend.infrastructure.di.handlers import HandlersProvider
from backend.infrastructure.di.persistence import PersistenceProvider
from backend.infrastructure.tools.converters import register_domain_converters
from backend.presentation.http.api.dependencies import ApiHandlers
from backend.presentation.http.api.dishka_providers import AuthDepsProvider, ExternalDepsProvider
from backend.presentation.http.api.middlewere.auth import AuthContextMiddleware, AuthzRoute
from backend.presentation.http.api.routing import api_router
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka


@dataclass(slots=True)
class ApiDependencies:
    auth_gateway: PersistenceGateway
    auth_jwt_verifier: JwtVerifier
    auth_authenticator: Authenticator
    auth_cache: StrCache
    handlers: ApiHandlers


@dataclass(slots=True)
class AuthDependencies:
    auth_gateway: PersistenceGateway
    auth_jwt_verifier: JwtVerifier
    auth_authenticator: Authenticator
    auth_cache: StrCache


def create_app(deps: ApiDependencies) -> FastAPI:
    register_domain_converters()
    app = FastAPI()
    app.state.auth_gateway = deps.auth_gateway
    app.state.auth_jwt_verifier = deps.auth_jwt_verifier
    app.state.auth_authenticator = deps.auth_authenticator
    app.state.auth_cache = deps.auth_cache
    app.state.handlers = deps.handlers

    container = make_async_container(
        PersistenceProvider(),
        HandlersProvider(),
        ExternalDepsProvider(deps),
    )
    setup_dishka(container, app)

    app.add_middleware(AuthContextMiddleware)
    app.router.route_class = AuthzRoute
    app.add_exception_handler(AppError, _app_error_handler)
    app.include_router(api_router)
    return app


def create_app_dishka(auth: AuthDependencies) -> FastAPI:
    register_domain_converters()
    app = FastAPI()
    app.state.auth_gateway = auth.auth_gateway
    app.state.auth_jwt_verifier = auth.auth_jwt_verifier
    app.state.auth_authenticator = auth.auth_authenticator
    app.state.auth_cache = auth.auth_cache

    container = make_async_container(
        PersistenceProvider(),
        HandlersProvider(),
        AuthDepsProvider(
            auth_gateway=auth.auth_gateway,
            auth_jwt_verifier=auth.auth_jwt_verifier,
            auth_authenticator=auth.auth_authenticator,
            auth_cache=auth.auth_cache,
        ),
    )
    setup_dishka(container, app)

    app.add_middleware(AuthContextMiddleware)
    app.router.route_class = AuthzRoute
    app.add_exception_handler(AppError, _app_error_handler)
    app.include_router(api_router)
    return app


def _app_error_handler(_request: Request, exc: Exception) -> Response:
    if not isinstance(exc, AppError):
        raise exc
    status_code = _status_for_code(exc.code)
    payload: dict[str, object] = {"code": exc.code, "message": exc.message}
    if exc.detail is not None:
        payload["detail"] = exc.detail
    if exc.meta is not None:
        payload["meta"] = exc.meta
    return JSONResponse(status_code=status_code, content=payload)


def _status_for_code(code: str) -> int:
    if code == "auth.unauthenticated":
        return 401
    if code == "auth.forbidden":
        return 403
    if code == "conflict":
        return 409
    if code.endswith(".not_found"):
        return 404
    return 400


__all__ = ["ApiDependencies", "AuthDependencies", "create_app", "create_app_dishka"]
