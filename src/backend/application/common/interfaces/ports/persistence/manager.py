from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from typing import Protocol, runtime_checkable


class SessionProtocol(Protocol): ...


type Query[T] = Callable[[SessionProtocol], Awaitable[T]]
type TransactionScope = AbstractAsyncContextManager[TransactionManager]


@runtime_checkable
class TransactionManager(Protocol):
    def transaction(self, *, nested: bool = False) -> TransactionScope: ...

    async def send[T](self, query: Query[T], /) -> T: ...
