from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Iterable

from fastapi_backend.domain.events.base import DomainEventHandler, DomainEventProtocol

logger = logging.getLogger(__name__)


class AsyncEventDispatcher:
    def __init__(self) -> None:
        self._async_handlers: dict[type, list[DomainEventHandler]] = {}

    def subscribe[E: DomainEventProtocol](
        self,
        event_type: type[E],
        handler: DomainEventHandler[E],
    ) -> None:
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []
        self._async_handlers[event_type].append(handler)

    async def publish(self, events: Iterable[DomainEventProtocol]) -> None:
        tasks: list[Awaitable[None]] = [
            self._safe_handle(handler, evt)
            for evt in events
            for handler in self._async_handlers.get(type(evt), [])
        ]
        if tasks:
            await asyncio.gather(*tasks)

    async def _safe_handle(self, handler: DomainEventHandler, event: DomainEventProtocol) -> None:
        try:
            await handler.handle(event)
        except Exception as e:
            logger.exception(
                f"Async handler {handler.__class__.__name__} failed for {type(event).__name__}: {e}"
            )

    def clear_subscriptions(self) -> None:
        self._async_handlers.clear()
