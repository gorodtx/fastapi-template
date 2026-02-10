from __future__ import annotations

import logging
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

_LOGGER = logging.getLogger(__name__)
_PUBLIC_META_FIELDS_BY_CODE: dict[str, tuple[str, ...]] = {
    "conflict": ("field",),
    "auth.too_many_requests": ("retry_after_s",),
}


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
    _LOGGER.warning(
        "Handled app error: code=%s detail=%r meta=%r",
        exc.code,
        exc.detail,
        exc.meta,
    )
    status_code = _status_for_code(exc.code)
    response = JSONResponse(
        status_code=status_code, content=_to_public_payload(exc)
    )
    retry_after = _read_retry_after(exc)
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
    return response


def _to_public_payload(exc: AppError) -> dict[str, object]:
    payload: dict[str, object] = {"code": exc.code, "message": exc.message}
    allowed_fields = _PUBLIC_META_FIELDS_BY_CODE.get(exc.code)
    if allowed_fields is None or exc.meta is None:
        return payload
    public_meta: dict[str, object] = {}
    for field in allowed_fields:
        value = exc.meta.get(field)
        if field == "field":
            if isinstance(value, str) and value.strip():
                public_meta[field] = value
        elif field == "retry_after_s" and isinstance(value, int) and value > 0:
            public_meta[field] = value
    if public_meta:
        payload["meta"] = public_meta
    return payload


def _read_retry_after(exc: AppError) -> int | None:
    if exc.code != "auth.too_many_requests" or exc.meta is None:
        return None
    retry_after = exc.meta.get("retry_after_s")
    if not isinstance(retry_after, int):
        return None
    if retry_after <= 0:
        return None
    return retry_after


def _status_for_code(code: str) -> int:
    if code == "auth.too_many_requests":
        return 429
    if code == "auth.unauthenticated":
        return 401
    if code in {"auth.forbidden", "rbac.hierarchy_violation"}:
        return 403
    if code in {"conflict", "rbac.role_unknown"}:
        return 409
    if code.endswith(".not_found"):
        return 404
    if code == "internal.error":
        return 500
    return 400
