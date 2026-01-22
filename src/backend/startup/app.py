from __future__ import annotations

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.application.common.exceptions.application import AppError
from backend.infrastructure.tools.converters import register_domain_converters
from backend.presentation.http.api.middlewere.auth import AuthContextMiddleware, AuthzRoute
from backend.presentation.http.api.routing import api_router
from backend.startup.di import setup_di


def create_app() -> FastAPI:
    register_domain_converters()
    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)
    setup_di(app)
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
