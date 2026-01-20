from __future__ import annotations

from typing import Literal, Protocol

from backend.application.common.dtos.base import DTO
from backend.application.common.exceptions.application import AppError
from backend.application.handlers.result import Result

HandlerMode = Literal["read", "write"]


class Handler[InDTO: DTO, OutDTO: DTO](Protocol):
    async def __call__(self, data: InDTO, /) -> Result[OutDTO, AppError]: ...


class CommandHandler[InDTO: DTO, OutDTO: DTO](Handler[InDTO, OutDTO], Protocol):
    """Marker protocol for command handlers."""


class QueryHandler[InDTO: DTO, OutDTO: DTO](Handler[InDTO, OutDTO], Protocol):
    """Marker protocol for query handlers."""
