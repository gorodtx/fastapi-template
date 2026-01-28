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
        object.__setattr__(self, "_id", id)

    @property
    def id(self: Entity) -> UUID:
        return self._id

    def __repr__(self: Entity) -> str:
        return f"{self.__class__.__name__}()"

    def __setattr__(self: Entity, name: str, value: object) -> None:
        if name == "_id" and hasattr(self, "_id") and self._id != value:
            raise AttributeError("Entity id is read-only")
        object.__setattr__(self, name, value)

    def __eq__(self: Entity, other: object) -> bool:
        if isinstance(other, Entity):
            return self.id == other.id
        return False

    def __hash__(self: Entity) -> int:
        return hash(self.id)
