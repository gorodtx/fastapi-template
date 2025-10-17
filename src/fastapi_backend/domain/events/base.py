from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

import uuid_utils.compat as uuid

from fastapi_backend.domain.core.entities.base import TypeID

TypeEventID = uuid.UUID


class DomainEventProtocol(Protocol):
    event_id: TypeEventID
    aggregate_id: TypeID
    occurred_at: datetime
    version: int

    def asdict(self) -> dict[str, Any]: ...


class DomainEventHandler[E: DomainEventProtocol](Protocol):
    async def handle(self, event: E) -> None: ...
