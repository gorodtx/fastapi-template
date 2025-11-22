from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass, fields
from typing import Any, Self, cast, dataclass_transform


@dataclass
class DTO:
    def asdict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_(cls, entity: Any) -> Self:
        if isinstance(entity, Mapping):
            return cls(**entity)
        attrs = {f.name: getattr(entity, f.name) for f in fields(cls)}
        return cls(**attrs)

    @classmethod
    def from_many(cls, entities: Iterable[Any]) -> list[Self]:
        return [cls.from_(e) for e in entities]


@dataclass_transform(
    kw_only_default=True,
)
def dto[T: DTO](
    _cls: type[T] | None = None,
    /,
    *,
    frozen: bool = True,
    slots: bool = True,
    kw_only: bool = True,
) -> Callable[[type[T]], type[T]] | type[T]:
    def wrap(cls: type[T]) -> type[T]:
        bases = (DTO, *cls.__bases__)
        namespace = dict(cls.__dict__)
        namespace.pop("__dict__", None)
        namespace.pop("__weakref__", None)
        new_cls = type(cls.__name__, bases, namespace)
        return cast(
            type[T],
            dataclass(frozen=frozen, slots=slots, kw_only=kw_only)(new_cls),
        )

    return wrap if _cls is None else wrap(_cls)
