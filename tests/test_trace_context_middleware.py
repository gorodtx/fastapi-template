from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.presentation.http.middleware import trace_context
from backend.presentation.http.middleware.trace_context import (
    trace_context_middleware,
)


def test_trace_header_added_when_trace_id_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    app.middleware("http")(trace_context_middleware)

    @app.get("/ok")
    async def ok() -> dict[str, bool]:
        return {"ok": True}

    monkeypatch.setattr(
        trace_context,
        "_read_trace_id",
        lambda: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )
    with TestClient(app) as client:
        response = client.get("/ok")
    assert response.status_code == 200
    assert (
        response.headers.get("X-Trace-Id")
        == "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    )


def test_trace_header_absent_when_trace_id_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    app.middleware("http")(trace_context_middleware)

    @app.get("/ok")
    async def ok() -> dict[str, bool]:
        return {"ok": True}

    monkeypatch.setattr(trace_context, "_read_trace_id", lambda: None)
    with TestClient(app) as client:
        response = client.get("/ok")
    assert response.status_code == 200
    assert response.headers.get("X-Trace-Id") is None
