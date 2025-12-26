from __future__ import annotations

from abc import abstractmethod
from typing import ClassVar, Literal, Protocol

from backend.application.common.dtos.base import DTO

HandlerMode = Literal["read", "write"]


class HandlerBase(Protocol):
    handler_mode: ClassVar[HandlerMode]


class CommandHandler[C: DTO, R: DTO](HandlerBase, Protocol):
    async def __call__(self, cmd: C, /) -> R:
        return await self._execute(cmd)

    @abstractmethod
    async def _execute(self, cmd: C, /) -> R:
        raise NotImplementedError


class QueryHandler[Q: DTO, R: DTO](HandlerBase, Protocol):
    async def __call__(self, query: Q, /) -> R:
        return await self._execute(query)

    @abstractmethod
    async def _execute(self, query: Q, /) -> R:
        raise NotImplementedError
