from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import TypeVar

from fastapi_backend.domain.events.base import DomainEventProtocol
from fastapi_backend.domain.ports.event_dispatcher import EventDispatcherPort

E = TypeVar("E", bound=DomainEventProtocol)
Handler = Callable[[E], None]


class EventDispatcher(EventDispatcherPort):
    def __init__(self) -> None:
        self._handlers: dict[
            type[DomainEventProtocol], list[Callable[[DomainEventProtocol], None]]
        ] = defaultdict(list)

    def register(self, event_type: type[E], handler: Handler[E]) -> None:
        self._handlers[event_type].append(handler)  # type: ignore[arg-type]

    def publish(self, events: Iterable[DomainEventProtocol]) -> None:
        for evt in events:
            for h in self._handlers.get(type(evt), []):
                h(evt)  # type: ignore[arg-type]
