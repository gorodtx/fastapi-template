from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast, dataclass_transform


class ValueObject: ...


@dataclass_transform(frozen_default=True, eq_default=True)
def value_object[V: ValueObject](
    *validate: Callable[[V], None],
) -> Callable[[type[V]], type[V]]:
    """A decorator for dataclass-based object values with optional validators."""

    def decorator(cls: type[V]) -> type[V]:
        namespace = dict(cls.__dict__)
        namespace.pop("__dict__", None)
        namespace.pop("__weakref__", None)

        if validate:

            def __post_init__(self: Any) -> None:
                instance = cast(V, self)
                for validator_fn in validate:
                    validator_fn(instance)

            namespace["__post_init__"] = __post_init__

        new_cls = type(cls.__name__, cls.__bases__, namespace)

        return cast(
            type[V],
            dataclass(
                frozen=True,
                eq=True,
                slots=True,
                repr=False,
            )(new_cls),
        )

    return decorator
