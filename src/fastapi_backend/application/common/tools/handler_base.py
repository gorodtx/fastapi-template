from __future__ import annotations

from abc import abstractmethod
from typing import Protocol

from fastapi_backend.application.common.dtos.base_dto import DTO
from fastapi_backend.domain.core.entities.base import Entity


class CommandHandler[C: DTO, R: DTO | Entity | None](Protocol):
    async def __call__(self, cmd: C) -> R:
        return await self._execute(cmd)

    @abstractmethod
    async def _execute(self, cmd: C, /) -> R:
        raise NotImplementedError


class QueryHandler[Q: DTO, R: DTO | None](Protocol):
    async def __call__(self, query: Q) -> R:
        return await self._execute(query)

    @abstractmethod
    async def _execute(self, query: Q, /) -> R:
        raise NotImplementedError
