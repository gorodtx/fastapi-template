from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import dataclass_transform, overload


class ValueObject:
    def __post_init__(self: ValueObject) -> None:
        return None


@dataclass_transform(frozen_default=True, eq_default=True)
@overload
def value_object[T: ValueObject](cls: type[T]) -> type[T]: ...


@overload
def value_object[T: ValueObject](
    *,
    validator: Callable[[T], None],
) -> Callable[[type[T]], type[T]]: ...


@dataclass_transform(frozen_default=True, eq_default=True)
def value_object[T: ValueObject](
    cls: type[T] | None = None,
    *,
    validator: Callable[[T], None] | None = None,
) -> type[T] | Callable[[type[T]], type[T]]:
    """Decorator for dataclass-based value objects with optional validator."""

    def decorate(inner_cls: type[T]) -> type[T]:
        if validator is None:
            return dataclass(
                frozen=True,
                eq=True,
                slots=True,
                repr=False,
            )(inner_cls)

        original_post_init: Callable[[T], None] = inner_cls.__post_init__
        validator_fn: Callable[[T], None] = validator

        def __post_init__(self: T) -> None:
            original_post_init(self)
            validator_fn(self)

        type.__setattr__(inner_cls, "__post_init__", __post_init__)

        return dataclass(
            frozen=True,
            eq=True,
            slots=True,
            repr=False,
        )(inner_cls)

    if cls is not None:
        return decorate(cls)

    return decorate
