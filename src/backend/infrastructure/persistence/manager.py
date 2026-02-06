from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from backend.application.common.interfaces.ports.persistence.manager import (
    Query,
    TransactionManager,
    TransactionScope,
)


class _NoopTxScope(AbstractAsyncContextManager["TransactionManagerImpl"]):
    __slots__: tuple[str, ...] = ("_tm",)

    def __init__(self: _NoopTxScope, tm: TransactionManagerImpl) -> None:
        self._tm = tm

    async def __aenter__(self: _NoopTxScope) -> TransactionManagerImpl:
        return self._tm

    async def __aexit__(
        self: _NoopTxScope,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None


class _TxScope(AbstractAsyncContextManager["TransactionManagerImpl"]):
    __slots__: tuple[str, ...] = ("_tm", "_tx")

    def __init__(
        self: _TxScope, tm: TransactionManagerImpl, tx: AsyncSessionTransaction
    ) -> None:
        self._tm = tm
        self._tx = tx

    async def __aenter__(self: _TxScope) -> TransactionManagerImpl:
        await self._tx.__aenter__()
        return self._tm

    async def __aexit__(
        self: _TxScope,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._tx.__aexit__(exc_type, exc_value, traceback)


class TransactionManagerImpl(TransactionManager):
    __slots__: tuple[str, ...] = ("conn",)

    def __init__(self: TransactionManagerImpl, conn: AsyncSession) -> None:
        self.conn = conn

    async def send[T](self: TransactionManagerImpl, query: Query[T], /) -> T:
        return await query(self.conn)

    __call__: Callable[
        [TransactionManagerImpl, Query[object]],
        Awaitable[object],
    ] = send

    def transaction(
        self: TransactionManagerImpl, *, nested: bool = False
    ) -> TransactionScope:
        if nested:
            if not self.conn.in_transaction():
                raise RuntimeError(
                    "Nested transaction requires an outer transaction"
                )
            return _TxScope(self, self.conn.begin_nested())

        if self.conn.in_transaction():
            return _NoopTxScope(self)

        return _TxScope(self, self.conn.begin())
