from __future__ import annotations

from typing import Protocol

from fastapi_backend.domain.events.base import DomainEventHandler, DomainEventProtocol


class EventDispatcherPort(Protocol):
    def subscribe[E: DomainEventProtocol](
        self,
        event_type: type[E],
        handler: DomainEventHandler[E],
    ) -> None: ...

    def publish(self, events: list[DomainEventProtocol]) -> None: ...

    def clear_subscriptions(self) -> None: ...
