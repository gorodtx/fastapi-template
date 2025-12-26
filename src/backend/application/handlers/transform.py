from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import dataclass_transform

from backend.application.handlers.base import HandlerBase, HandlerMode


@dataclass_transform(frozen_default=True, eq_default=True)
def handler[H: HandlerBase](*, mode: HandlerMode) -> Callable[[type[H]], type[H]]:
    """Decorator for command/query handlers with frozen dataclass."""

    def decorate(cls: type[H]) -> type[H]:
        wrapped = dataclass(
            frozen=True,
            eq=True,
            slots=True,
            kw_only=True,
        )(cls)
        wrapped.handler_mode = mode
        return wrapped

    return decorate
