from __future__ import annotations

from dataclasses import dataclass

from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram


@dataclass(slots=True)
class CustomMetrics:
    outbox_processed_total: Counter
    outbox_retry_total: Counter
    outbox_dead_total: Counter
    outbox_delivery_latency_seconds: Histogram
    outbox_lag_seconds: Histogram
    outbox_relay_batch_size: Histogram
    celery_task_duration_seconds: Histogram
    celery_task_retries_total: Counter

    @staticmethod
    def build() -> CustomMetrics:
        meter = metrics.get_meter("backend.observability")
        return CustomMetrics(
            outbox_processed_total=meter.create_counter(
                "outbox_processed_total",
                description="Total count of processed outbox events.",
            ),
            outbox_retry_total=meter.create_counter(
                "outbox_retry_total",
                description="Total count of outbox retries.",
            ),
            outbox_dead_total=meter.create_counter(
                "outbox_dead_total",
                description="Total count of outbox dead-lettered events.",
            ),
            outbox_delivery_latency_seconds=meter.create_histogram(
                "outbox_delivery_latency_seconds",
                unit="s",
                description=(
                    "Latency from event creation to successful delivery."
                ),
            ),
            outbox_lag_seconds=meter.create_histogram(
                "outbox_lag_seconds",
                unit="s",
                description=(
                    "Lag between event creation and relay pickup timestamp."
                ),
            ),
            outbox_relay_batch_size=meter.create_histogram(
                "outbox_relay_batch_size",
                description="Relay batch sizes for outbox polling.",
            ),
            celery_task_duration_seconds=meter.create_histogram(
                "celery_task_duration_seconds",
                unit="s",
                description="Duration of celery task execution.",
            ),
            celery_task_retries_total=meter.create_counter(
                "celery_task_retries_total",
                description="Total count of celery task retries.",
            ),
        )
