from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import dataclass_transform, overload


@dataclass(frozen=True, slots=True)
class DTO: ...


@dataclass_transform(
    frozen_default=True,
    kw_only_default=True,
)
@overload
def dto[TDTO: DTO](cls: type[TDTO], /) -> type[TDTO]: ...


@overload
def dto[TDTO: DTO](
    _cls: None = None,
    /,
    *,
    frozen: bool = True,
    slots: bool = True,
    kw_only: bool = True,
) -> Callable[[type[TDTO]], type[TDTO]]: ...


def dto[TDTO: DTO](
    _cls: type[TDTO] | None = None,
    /,
    *,
    frozen: bool = True,
    slots: bool = True,
    kw_only: bool = True,
) -> Callable[[type[TDTO]], type[TDTO]] | type[TDTO]:
    def wrap(cls: type[TDTO]) -> type[TDTO]:
        return dataclass(frozen=frozen, slots=slots, kw_only=kw_only)(cls)

    return wrap if _cls is None else wrap(_cls)
