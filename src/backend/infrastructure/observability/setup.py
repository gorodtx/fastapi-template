from __future__ import annotations

import os
from collections.abc import Sequence

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.view import (
    ExplicitBucketHistogramAggregation,
    View,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_ON,
    Sampler,
    TraceIdRatioBased,
)

from backend.infrastructure.observability.config import ObservabilityConfig
from backend.infrastructure.observability.metrics import CustomMetrics

_HTTP_DURATION_BUCKETS: Sequence[float] = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.075,
    0.1,
    0.25,
    0.5,
    0.75,
    1.0,
    2.5,
    5.0,
    7.5,
    10.0,
)


def setup_observability(
    app: FastAPI,
    cfg: ObservabilityConfig,
) -> None:
    if not cfg.enabled:
        return
    if cfg.semconv_stability_opt_in:
        os.environ.setdefault(
            "OTEL_SEMCONV_STABILITY_OPT_IN",
            cfg.semconv_stability_opt_in,
        )
    if cfg.capture_request_headers:
        os.environ.setdefault(
            "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST",
            ".*",
        )
    if cfg.capture_response_headers:
        os.environ.setdefault(
            "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE",
            ".*",
        )
    if cfg.sanitize_fields_csv:
        os.environ.setdefault(
            "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SANITIZE_FIELDS",
            cfg.sanitize_fields_csv,
        )

    resource = Resource.create(
        {
            "service.name": cfg.service_name,
            "service.version": cfg.service_version,
            "deployment.environment.name": cfg.environment,
        }
    )
    insecure = _is_insecure_endpoint(cfg.otlp_endpoint)
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=_build_sampler(cfg),
    )
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=cfg.otlp_endpoint,
                insecure=insecure,
            )
        )
    )
    trace.set_tracer_provider(tracer_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=cfg.otlp_endpoint,
            insecure=insecure,
        ),
        export_interval_millis=cfg.metrics_export_interval_ms,
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
        views=[
            View(
                instrument_name="http.server.request.duration",
                aggregation=ExplicitBucketHistogramAggregation(
                    boundaries=_HTTP_DURATION_BUCKETS
                ),
            )
        ],
    )
    metrics.set_meter_provider(meter_provider)
    app.state.custom_metrics = CustomMetrics.build()

    if cfg.http_instrumentation_enabled:
        FastAPIInstrumentor.instrument_app(app)

    _register_shutdown(app, tracer_provider, meter_provider)


def _register_shutdown(
    app: FastAPI,
    tracer_provider: TracerProvider,
    meter_provider: MeterProvider,
) -> None:
    async def _shutdown() -> None:
        meter_provider.shutdown()
        tracer_provider.shutdown()

    app.add_event_handler("shutdown", _shutdown)


def _is_insecure_endpoint(endpoint: str | None) -> bool:
    if endpoint is None:
        return False
    return endpoint.startswith("http://")


def _build_sampler(cfg: ObservabilityConfig) -> Sampler:
    if cfg.traces_sampler == "always_on":
        return ALWAYS_ON
    if cfg.traces_sampler == "traceidratio":
        return TraceIdRatioBased(cfg.traces_sampler_arg)
    return TraceIdRatioBased(0.1)
