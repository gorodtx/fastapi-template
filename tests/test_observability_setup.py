from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from pytest import MonkeyPatch
from sqlalchemy.ext.asyncio import create_async_engine

from backend.infrastructure.observability import (
    setup as observability_setup_module,
)
from backend.infrastructure.observability.config import ObservabilityConfig
from backend.infrastructure.observability.setup import (
    instrument_sqlalchemy_engine,
    setup_observability,
)


def test_setup_observability_noop_when_disabled() -> None:
    app = FastAPI()
    cfg = ObservabilityConfig(
        enabled=False,
        service_name="backend",
        service_version="0.1.0",
        environment="test",
        otlp_endpoint=None,
        otlp_headers=None,
        otlp_ca_cert_file=None,
        otlp_client_cert_file=None,
        otlp_client_key_file=None,
        metrics_export_interval_ms=15000,
        traces_sampler="traceidratio",
        traces_sampler_arg=0.1,
        http_instrumentation_enabled=True,
        sqlalchemy_instrumentation_enabled=False,
        redis_instrumentation_enabled=False,
        capture_request_headers=False,
        capture_response_headers=False,
        sanitize_fields_csv="",
        semconv_stability_opt_in=None,
    )
    setup_observability(app, cfg)
    assert not hasattr(app.state, "custom_metrics")


def test_setup_observability_enables_redis_instrumentation(
    monkeypatch: MonkeyPatch,
) -> None:
    app = FastAPI()
    calls: dict[str, int] = {"count": 0}

    class _FakeRedisInstrumentor:
        def instrument(self) -> None:
            calls["count"] += 1

    monkeypatch.setattr(
        observability_setup_module,
        "RedisInstrumentor",
        _FakeRedisInstrumentor,
    )
    monkeypatch.setattr(
        observability_setup_module,
        "_INSTRUMENTATION_STATE",
        {
            "redis_instrumented": False,
            "logging_instrumented": True,
        },
    )
    monkeypatch.setattr(
        observability_setup_module,
        "_build_logger_provider",
        lambda *_args, **_kwargs: _FakeLoggerProvider(),
    )
    cfg = ObservabilityConfig(
        enabled=True,
        service_name="backend",
        service_version="0.1.0",
        environment="test",
        otlp_endpoint=None,
        otlp_headers=None,
        otlp_ca_cert_file=None,
        otlp_client_cert_file=None,
        otlp_client_key_file=None,
        metrics_export_interval_ms=15000,
        traces_sampler="traceidratio",
        traces_sampler_arg=0.1,
        http_instrumentation_enabled=False,
        sqlalchemy_instrumentation_enabled=False,
        redis_instrumentation_enabled=True,
        capture_request_headers=False,
        capture_response_headers=False,
        sanitize_fields_csv="",
        semconv_stability_opt_in=None,
    )
    setup_observability(app, cfg)
    assert calls["count"] == 1


class _FakeLoggerProvider:
    def shutdown(self) -> None:
        return None


def test_instrument_logging_requires_logging_package(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        observability_setup_module,
        "_INSTRUMENTATION_STATE",
        {
            "redis_instrumented": False,
            "logging_instrumented": False,
        },
    )

    def _missing_import(_name: str) -> object:
        raise ModuleNotFoundError("missing module")

    monkeypatch.setattr(
        observability_setup_module,
        "import_module",
        _missing_import,
    )

    with pytest.raises(
        RuntimeError,
        match="opentelemetry-instrumentation-logging",
    ):
        observability_setup_module._instrument_logging()


def test_instrument_sqlalchemy_engine_idempotent(
    monkeypatch: MonkeyPatch,
) -> None:
    calls: list[object] = []

    class _FakeSQLAlchemyInstrumentor:
        def instrument(self, *, engine: object) -> None:
            calls.append(engine)

    monkeypatch.setattr(
        observability_setup_module,
        "SQLAlchemyInstrumentor",
        _FakeSQLAlchemyInstrumentor,
    )
    monkeypatch.setattr(
        observability_setup_module,
        "_SQLALCHEMY_INSTRUMENTED_ENGINES",
        set(),
    )
    engine = create_async_engine("postgresql+asyncpg://u:p@127.0.0.1:5432/db")
    try:
        instrument_sqlalchemy_engine(engine)
        instrument_sqlalchemy_engine(engine)
        assert calls == [engine.sync_engine]
    finally:
        asyncio.run(engine.dispose())
