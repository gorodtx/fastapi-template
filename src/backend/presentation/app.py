from __future__ import annotations

import os

from dishka.integrations.fastapi import DishkaRoute
from environs import Env
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.application.common.exceptions.application import AppError
from backend.domain.core.constants.serialization import (
    register_domain_converters,
)
from backend.presentation.di.container import setup_di
from backend.presentation.di.startup_checks import assert_closed_by_default
from backend.presentation.http.api.routing.router import api_router
from backend.presentation.settings import Settings, is_prod_env


def create_app() -> FastAPI:
    register_domain_converters()
    env = Env()
    if os.environ.get("APP_ENV", "").lower() not in {"prod", "production"}:
        env.read_env()
    settings = Settings.from_env(env)

    docs_enabled = not is_prod_env(settings)
    app = FastAPI(
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    setup_di(app, settings)
    app.router.route_class = DishkaRoute
    app.add_exception_handler(AppError, _app_error_handler)
    app.include_router(api_router)
    assert_closed_by_default(app)
    return app


def _app_error_handler(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, AppError):
        raise exc
    request.scope["backend.rollback_only"] = True
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
