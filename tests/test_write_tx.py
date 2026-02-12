from __future__ import annotations

from dataclasses import dataclass

import pytest

from backend.application.common.exceptions.application import (
    AppError,
    UnauthenticatedError,
)
from backend.application.handlers.result import Result, ResultImpl
from backend.presentation.http.api.tx import run_write_in_tx


@dataclass(slots=True)
class _TxScope:
    entered: bool = False
    exited: bool = False
    seen_exc: type[BaseException] | None = None

    async def __aenter__(self: _TxScope) -> None:
        self.entered = True

    async def __aexit__(
        self: _TxScope,
        exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: object,
    ) -> None:
        self.exited = True
        self.seen_exc = exc_type


@dataclass(slots=True)
class _SessionStub:
    tx: _TxScope

    def begin(self: _SessionStub) -> _TxScope:
        return self.tx


@pytest.mark.asyncio
async def test_run_write_in_tx_unwraps_ok_result() -> None:
    session = _SessionStub(tx=_TxScope())

    async def action() -> Result[int, AppError]:
        return ResultImpl.ok(7, AppError)

    value = await run_write_in_tx(session, action())

    assert value == 7
    assert session.tx.entered is True
    assert session.tx.exited is True
    assert session.tx.seen_exc is None


@pytest.mark.asyncio
async def test_run_write_in_tx_rolls_back_on_err_result() -> None:
    session = _SessionStub(tx=_TxScope())

    async def action() -> Result[int, AppError]:
        return ResultImpl.err_app(UnauthenticatedError(), int)

    with pytest.raises(UnauthenticatedError):
        await run_write_in_tx(session, action())

    assert session.tx.entered is True
    assert session.tx.exited is True
    assert session.tx.seen_exc is UnauthenticatedError
