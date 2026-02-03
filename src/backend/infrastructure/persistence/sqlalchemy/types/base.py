from __future__ import annotations

from collections.abc import Callable
from typing import overload

from backend.domain.core.constants.serialization import StrValueObject


@overload
def bind_vo[T: StrValueObject](
    value: None, expected_type: type[T]
) -> None: ...


@overload
def bind_vo[T: StrValueObject](value: T, expected_type: type[T]) -> str: ...


def bind_vo(
    value: StrValueObject | None, expected_type: type[object]
) -> str | None:
    if value is None:
        return None
    vo_value: StrValueObject = value
    if not isinstance(vo_value, expected_type):
        raise TypeError(
            f"Expected {expected_type.__name__}, got {type(vo_value).__name__}"
        )
    return vo_value.value


def result_vo[T: StrValueObject](
    value: str | None,
    vo_ctor: Callable[[str], T],
) -> T | None:
    if value is None:
        return None
    return vo_ctor(value)
