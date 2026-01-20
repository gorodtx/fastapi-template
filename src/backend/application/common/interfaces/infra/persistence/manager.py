from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

type Query[T] = Callable[[AsyncSession], Awaitable[T]]


@runtime_checkable
class TransactionManager(Protocol):
    def transaction(self, *, nested: bool = False) -> TransactionScope: ...

    async def send[T](self, query: Query[T], /) -> T: ...


type TransactionScope = AbstractAsyncContextManager[TransactionManager]
