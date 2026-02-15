from __future__ import annotations

from contextlib import AbstractAsyncContextManager, nullcontext
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from backend.application.common.interfaces.ports.persistence.manager import (
    Query,
    TransactionManager,
    TransactionScope,
)


class _ManagedTxScope(AbstractAsyncContextManager["TransactionManagerImpl"]):
    __slots__: tuple[str, ...] = ("_tm", "_tx")

    def __init__(
        self: _ManagedTxScope,
        tm: TransactionManagerImpl,
        *,
        tx: AsyncSessionTransaction | None = None,
    ) -> None:
        self._tm = tm
        self._tx = tx

    async def __aenter__(self: _ManagedTxScope) -> TransactionManagerImpl:
        self._tm.enter_scope()
        if self._tx is not None:
            await self._tx.__aenter__()
        return self._tm

    async def __aexit__(
        self: _ManagedTxScope,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if self._tx is not None:
                await self._tx.__aexit__(exc_type, exc_value, traceback)
                return None
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
            return _ManagedTxScope(
                self,
                tx=self.conn.begin_nested(),
            )

        if self._scope_depth > 0:
            return nullcontext(self)

        if self.conn.in_transaction():
            return _ManagedTxScope(self)

        return _ManagedTxScope(
            self,
            tx=self.conn.begin(),
        )
