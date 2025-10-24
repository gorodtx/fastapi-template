from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import dataclass_transform


@dataclass_transform(frozen_default=True, eq_default=True)
def value_object[V: "ValueObject"](*validate: Callable[[V], None]) -> Callable[[type[V]], type[V]]:
    def decorator(cls: type[V]) -> type[V]:
        if validate:

            def __post_init__(self: V) -> None:
                for validator_fn in validate:
                    validator_fn(self)

            cls.__post_init__ = __post_init__  # type: ignore

        decorated_cls = dataclass(frozen=True, eq=True, slots=True, repr=False)(cls)

        return decorated_cls

    return decorator


class ValueObject: ...
