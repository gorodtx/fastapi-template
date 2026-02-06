from __future__ import annotations

from typing import Protocol


class MetricsCollector(Protocol):
    def increment(
        self: MetricsCollector, key: str, *, value: float = 1.0
    ) -> None: ...

    def observe(self: MetricsCollector, key: str, value: float) -> None: ...

    def snapshot(self: MetricsCollector) -> dict[str, float]: ...
