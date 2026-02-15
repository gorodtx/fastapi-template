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
        self._tm.enter_scope()
        await self._tx.__aenter__()
        return self._tm

    async def __aexit__(
        self: _TxScope,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            await self._tx.__aexit__(exc_type, exc_value, traceback)
        finally:
            self._tm.leave_scope()


class _CurrentTxScope(AbstractAsyncContextManager["TransactionManagerImpl"]):
    __slots__: tuple[str, ...] = ("_tm",)

    def __init__(self: _CurrentTxScope, tm: TransactionManagerImpl) -> None:
        self._tm = tm

    async def __aenter__(self: _CurrentTxScope) -> TransactionManagerImpl:
        self._tm.enter_scope()
        return self._tm

    async def __aexit__(
        self: _CurrentTxScope,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if not self._tm.conn.in_transaction():
                return None
            if exc_type is None:
                await self._tm.conn.commit()
            else:
                await self._tm.conn.rollback()
        finally:
            self._tm.leave_scope()
        return None


class TransactionManagerImpl(TransactionManager):
    __slots__: tuple[str, ...] = ("_scope_depth", "conn")

    def __init__(self: TransactionManagerImpl, conn: AsyncSession) -> None:
        self.conn = conn
        self._scope_depth = 0

    async def send[T](self: TransactionManagerImpl, query: Query[T], /) -> T:
        return await query(self.conn)

    __call__: Callable[
        [TransactionManagerImpl, Query[object]],
        Awaitable[object],
    ] = send

    def enter_scope(self: TransactionManagerImpl) -> None:
        self._scope_depth += 1

    def leave_scope(self: TransactionManagerImpl) -> None:
        if self._scope_depth <= 0:
            raise RuntimeError("Transaction scope depth underflow")
        self._scope_depth -= 1

    def transaction(
        self: TransactionManagerImpl, *, nested: bool = False
    ) -> TransactionScope:
        if nested:
            if not self.conn.in_transaction():
                raise RuntimeError(
                    "Nested transaction requires an outer transaction"
                )
            return _TxScope(self, self.conn.begin_nested())

        if self._scope_depth > 0:
            return _NoopTxScope(self)

        if self.conn.in_transaction():
            return _CurrentTxScope(self)

        return _TxScope(self, self.conn.begin())
