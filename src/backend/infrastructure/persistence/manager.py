from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from backend.application.common.interfaces.infra.persistence.manager import (
    Query,
    TransactionManager,
    TransactionScope,
)


class _TxScope(AbstractAsyncContextManager["TransactionManagerImpl"]):
    __slots__ = ("_tm", "_tx")

    def __init__(self, tm: TransactionManagerImpl, tx: AsyncSessionTransaction) -> None:
        self._tm = tm
        self._tx = tx

    async def __aenter__(self) -> TransactionManagerImpl:
        await self._tx.__aenter__()
        return self._tm

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._tx.__aexit__(exc_type, exc_value, traceback)


class TransactionManagerImpl(TransactionManager):
    __slots__ = ("conn",)

    def __init__(self, conn: AsyncSession) -> None:
        self.conn = conn

    async def send[T](self, query: Query[T], /) -> T:
        return await query(self.conn)

    __call__ = send

    def transaction(self, *, nested: bool = False) -> TransactionScope:
        if nested:
            if not self.conn.in_transaction():
                raise RuntimeError("Nested transaction requires an outer transaction")
            tx = self.conn.begin_nested()
        else:
            if self.conn.in_transaction():
                raise RuntimeError("Outer transaction already started; use nested=True")
            tx = self.conn.begin()
        return _TxScope(self, tx)
