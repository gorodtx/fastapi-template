from __future__ import annotations

from fastapi import FastAPI

from backend.infrastructure.observability.config import ObservabilityConfig
from backend.infrastructure.observability.setup import setup_observability


def test_setup_observability_noop_when_disabled() -> None:
    app = FastAPI()
    cfg = ObservabilityConfig(
        enabled=False,
        service_name="backend",
        service_version="0.1.0",
        environment="test",
        otlp_endpoint=None,
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
