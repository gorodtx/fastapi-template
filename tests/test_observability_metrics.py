from __future__ import annotations

from backend.infrastructure.observability.metrics import CustomMetrics


def test_custom_metrics_build() -> None:
    metrics = CustomMetrics.build()
    metrics.outbox_processed_total.add(1, {"result": "success"})
    metrics.outbox_retry_total.add(1, {"reason": "transient"})
    metrics.outbox_dead_total.add(1, {"reason": "permanent"})
    metrics.outbox_delivery_latency_seconds.record(0.5)
    metrics.outbox_lag_seconds.record(0.1)
    metrics.outbox_relay_batch_size.record(10)
    metrics.celery_task_duration_seconds.record(
        0.2, {"task_name": "test", "status": "ok"}
    )
    metrics.celery_task_retries_total.add(1, {"task_name": "test"})
