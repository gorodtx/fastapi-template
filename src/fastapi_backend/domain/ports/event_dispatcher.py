from __future__ import annotations

from typing import Protocol

from fastapi_backend.domain.events.base import DomainEventHandler, DomainEventProtocol


class EventDispatcherPort(Protocol):
    async def subscribe[E: DomainEventProtocol](
        self,
        event_type: type[E],
        handler: DomainEventHandler[E],
    ) -> None: ...

    async def publish(self, events: list[DomainEventProtocol]) -> None: ...

    async def clear_subscriptions(self) -> None: ...
