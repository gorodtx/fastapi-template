from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, TypeVar, dataclass_transform

HandlerMode = Literal["write", "read"]


class HandlerClass(Protocol):
    __handler_mode__: HandlerMode


H = TypeVar("H", bound=HandlerClass)


@dataclass_transform(frozen_default=True, eq_default=True)
def handler(*, mode: HandlerMode):
    def decorate[H: HandlerClass](cls: type[H]) -> type[H]:
        cls = dataclass(frozen=True, eq=True, slots=True, kw_only=True)(cls)
        cls.__handler_mode__ = mode
        return cls

    return decorate
