from __future__ import annotations

from dataclasses import dataclass
from typing import dataclass_transform

from uuid_utils.compat import UUID


@dataclass_transform(eq_default=False)
def entity[T](cls: type[T]) -> type[T]:
    return dataclass(eq=False, init=False, repr=False)(cls)


@entity
class Entity:
    _id: UUID

    def __init__(self: Entity, *, id: UUID) -> None:
        self._id = id

    @property
    def id(self: Entity) -> UUID:
        return self._id

    def __repr__(self: Entity) -> str:
        return f"{self.__class__.__name__}()"

    def __eq__(self: Entity, other: object) -> bool:
        if isinstance(other, Entity):
            return self.id == other.id
        return False

    def __hash__(self: Entity) -> int:
        return hash(self.id)
