from __future__ import annotations

from typing import Literal, Protocol

from backend.application.common.dtos.base import DTO
from backend.application.common.exceptions.application import AppError
from backend.application.handlers.result import Result

type HandlerMode = Literal["read", "write"]


class HandlerBase(Protocol):
    """Marker protocol for handlers."""


class Handler[InDTO: DTO, OutDTO: DTO](HandlerBase, Protocol):
    async def __call__(
        self: Handler[InDTO, OutDTO], data: InDTO, /
    ) -> Result[OutDTO, AppError]: ...


class CommandHandler[InDTO: DTO, OutDTO: DTO](
    Handler[InDTO, OutDTO], Protocol
):
    """Marker protocol for command handlers."""


class QueryHandler[InDTO: DTO, OutDTO: DTO](Handler[InDTO, OutDTO], Protocol):
    """Marker protocol for query handlers."""
