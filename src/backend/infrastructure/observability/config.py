from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ObservabilityConfig:
    enabled: bool
    service_name: str
    service_version: str
    environment: str
    otlp_endpoint: str | None
    otlp_headers: str | None
    otlp_ca_cert_file: str | None
    otlp_client_cert_file: str | None
    otlp_client_key_file: str | None
    metrics_export_interval_ms: int
    traces_sampler: str
    traces_sampler_arg: float
    http_instrumentation_enabled: bool
    sqlalchemy_instrumentation_enabled: bool
    redis_instrumentation_enabled: bool
    capture_request_headers: bool
    capture_response_headers: bool
    sanitize_fields_csv: str
    semconv_stability_opt_in: str | None
