from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, dataclass_transform

import uuid_utils.compat as uuid
from msgspec import to_builtins

TypeID = uuid.UUID


@dataclass_transform()
def entity[E](cls: type[E]) -> type[E]:
    return dataclass(kw_only=True)(cls)


@entity
class Entity:
    id: TypeID
    _pending_events: list[Any] = field(default_factory=list, init=False, repr=False)

    def _raise_event(self, event: Any) -> None:
        self._pending_events.append(event)

    def pull_events(self) -> list[Any]:
        events = self._pending_events[:]
        self._pending_events.clear()
        return events

    def asdict(self) -> dict[str, Any]:
        return to_builtins(self, str_keys=True)
