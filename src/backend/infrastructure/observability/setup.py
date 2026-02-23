from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from threading import Lock

from fastapi import FastAPI
from grpc import ChannelCredentials, ssl_channel_credentials
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import (
    SQLAlchemyInstrumentor,
)
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
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.infrastructure.observability.config import ObservabilityConfig

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
_INSTRUMENTATION_LOCK = Lock()
_SQLALCHEMY_INSTRUMENTED_ENGINES: set[int] = set()
_INSTRUMENTATION_STATE: dict[str, bool] = {"redis_instrumented": False}


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
    credentials = _build_grpc_credentials(cfg)
    insecure = _is_insecure_endpoint(cfg.otlp_endpoint, credentials)
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=_build_sampler(cfg),
    )
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=cfg.otlp_endpoint,
                headers=cfg.otlp_headers,
                insecure=insecure,
                credentials=credentials,
            )
        )
    )
    trace.set_tracer_provider(tracer_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=cfg.otlp_endpoint,
            headers=cfg.otlp_headers,
            insecure=insecure,
            credentials=credentials,
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

    if cfg.http_instrumentation_enabled:
        FastAPIInstrumentor.instrument_app(app)
    if cfg.redis_instrumentation_enabled:
        _instrument_redis()

    _register_shutdown(app, tracer_provider, meter_provider)


def instrument_sqlalchemy_engine(engine: AsyncEngine) -> None:
    engine_id = id(engine.sync_engine)
    with _INSTRUMENTATION_LOCK:
        if engine_id in _SQLALCHEMY_INSTRUMENTED_ENGINES:
            return
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
        _SQLALCHEMY_INSTRUMENTED_ENGINES.add(engine_id)


def _register_shutdown(
    app: FastAPI,
    tracer_provider: TracerProvider,
    meter_provider: MeterProvider,
) -> None:
    async def _shutdown() -> None:
        meter_provider.shutdown()
        tracer_provider.shutdown()

    app.add_event_handler("shutdown", _shutdown)


def _is_insecure_endpoint(
    endpoint: str | None, credentials: ChannelCredentials | None
) -> bool:
    if credentials is not None:
        if endpoint is not None and endpoint.startswith("http://"):
            raise RuntimeError(
                "OBS_OTEL_EXPORTER_OTLP_ENDPOINT must use https/grpc when TLS credentials are configured"
            )
        return False
    if endpoint is None:
        return False
    return endpoint.startswith("http://")


def _build_sampler(cfg: ObservabilityConfig) -> Sampler:
    if cfg.traces_sampler == "always_on":
        return ALWAYS_ON
    if cfg.traces_sampler == "traceidratio":
        return TraceIdRatioBased(cfg.traces_sampler_arg)
    return TraceIdRatioBased(0.1)


def _build_grpc_credentials(
    cfg: ObservabilityConfig,
) -> ChannelCredentials | None:
    has_tls_material = (
        cfg.otlp_ca_cert_file is not None
        or cfg.otlp_client_cert_file is not None
        or cfg.otlp_client_key_file is not None
    )
    if not has_tls_material:
        return None
    if (cfg.otlp_client_cert_file is None) != (
        cfg.otlp_client_key_file is None
    ):
        raise RuntimeError(
            "OBS_OTEL_EXPORTER_OTLP_CLIENT_CERT_FILE and OBS_OTEL_EXPORTER_OTLP_CLIENT_KEY_FILE must be set together"
        )
    root_certificates = _read_bytes(cfg.otlp_ca_cert_file)
    certificate_chain = _read_bytes(cfg.otlp_client_cert_file)
    private_key = _read_bytes(cfg.otlp_client_key_file)
    return ssl_channel_credentials(
        root_certificates=root_certificates,
        private_key=private_key,
        certificate_chain=certificate_chain,
    )


def _read_bytes(path: str | None) -> bytes | None:
    if path is None:
        return None
    return Path(path).read_bytes()


def _instrument_redis() -> None:
    with _INSTRUMENTATION_LOCK:
        if _INSTRUMENTATION_STATE["redis_instrumented"]:
            return
        RedisInstrumentor().instrument()
        _INSTRUMENTATION_STATE["redis_instrumented"] = True
