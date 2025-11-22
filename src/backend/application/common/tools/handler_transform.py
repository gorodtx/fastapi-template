from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, dataclass_transform

from backend.application.common.tools.handler_base import CommandHandler, QueryHandler

type AnyHandler = CommandHandler | QueryHandler
type HandlerMode = Literal["read", "write"]


@dataclass_transform(frozen_default=True, eq_default=True)
def handler(*, mode: HandlerMode) -> Callable[[type[AnyHandler]], type[AnyHandler]]:
    """Decorator for command/query handlers with frozen dataclass."""

    def decorate[H: AnyHandler](cls: type[H]) -> type[H]:
        cls = dataclass(frozen=True, eq=True, slots=True, kw_only=True)(cls)
        cls._handler_mode = mode  # type: ignore[attr-defined]
        return cls

    return decorate
