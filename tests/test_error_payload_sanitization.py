from __future__ import annotations

import json

from starlette.requests import Request
from starlette.responses import Response

from backend.application.common.exceptions.application import (
    AppError,
    ConflictError,
    TooManyRequestsError,
)
from backend.presentation.app import _app_error_handler


def _request() -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "query_string": b"",
        "headers": [],
    }
    return Request(scope)


def _payload(response: Response) -> dict[str, object]:
    raw_payload = json.loads(response.body.decode("utf-8"))
    if not isinstance(raw_payload, dict):
        raise AssertionError("Expected a JSON object payload")
    out: dict[str, object] = {}
    for key, value in raw_payload.items():
        if isinstance(key, str):
            out[key] = value
    return out


def test_conflict_payload_exposes_only_safe_meta_fields() -> None:
    response = _app_error_handler(
        _request(),
        ConflictError(
            "Resource already exists",
            detail="INSERT INTO users(password_hash=...)",
            meta={"field": "email", "sqlstate": "23505"},
        ),
    )
    payload = _payload(response)

    assert response.status_code == 409
    assert payload["code"] == "conflict"
    assert payload["message"] == "Resource already exists"
    assert payload["meta"] == {"field": "email"}
    assert "detail" not in payload


def test_internal_error_payload_does_not_expose_detail_or_meta() -> None:
    response = _app_error_handler(
        _request(),
        AppError(
            code="internal.error",
            message="Internal server error",
            detail="db timeout",
            meta={"sqlstate": "08006"},
        ),
    )
    payload = _payload(response)

    assert response.status_code == 500
    assert payload == {
        "code": "internal.error",
        "message": "Internal server error",
    }


def test_too_many_requests_sets_retry_after_header() -> None:
    response = _app_error_handler(
        _request(), TooManyRequestsError(retry_after_s=7)
    )
    payload = _payload(response)

    assert response.status_code == 429
    assert response.headers.get("Retry-After") == "7"
    assert payload["code"] == "auth.too_many_requests"
    assert payload["message"] == "Too many requests"
    assert payload["meta"] == {"retry_after_s": 7}
