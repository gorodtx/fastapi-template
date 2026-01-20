from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from typing import dataclass_transform, overload


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


class DTO:
    __slots__ = ()

    def as_mapping(
        self,
        *,
        exclude_none: bool = False,
        exclude: set[str] | None = None,
    ) -> Mapping[str, object]:
        if not is_dataclass(self):
            raise TypeError("DTO must be a dataclass (use @dto decorator on subclasses)")

        ex = exclude or set()
        d = {f.name: getattr(self, f.name) for f in fields(self) if f.name not in ex}
        if exclude_none:
            d = {k: v for k, v in d.items() if v is not None}
        return d
