from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, overload


class HasStrValue(Protocol):
    @property
    def value(self: HasStrValue) -> str: ...


@overload
def bind_vo[T: HasStrValue](value: None, expected_type: type[T]) -> None: ...


@overload
def bind_vo[T: HasStrValue](value: T, expected_type: type[T]) -> str: ...


def bind_vo(
    value: HasStrValue | None, expected_type: type[object]
) -> str | None:
    if value is None:
        return None
    vo_value: HasStrValue = value
    if not isinstance(vo_value, expected_type):
        raise TypeError(
            f"Expected {expected_type.__name__}, got {type(vo_value).__name__}"
        )
    return vo_value.value


def result_vo[T: HasStrValue](
    value: str | None,
    vo_ctor: Callable[[str], T],
) -> T | None:
    if value is None:
        return None
    return vo_ctor(value)
