from __future__ import annotations

from dataclasses import dataclass

import pytest

from backend.application.common.exceptions.application import (
    UnauthenticatedError,
)
from backend.application.common.tools.tx_result import run_result_in_tx
from backend.application.handlers.result import ResultImpl


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
class _ManagerStub:
    tx: _TxScope

    def transaction(self: _ManagerStub, *, nested: bool = False) -> _TxScope:
        _ = nested
        return self.tx


@pytest.mark.asyncio
async def test_run_result_in_tx_unwraps_ok_result() -> None:
    manager = _ManagerStub(tx=_TxScope())

    async def action() -> object:
        return ResultImpl.ok(17, UnauthenticatedError)

    result = await run_result_in_tx(manager, action())

    assert result.is_ok()
    assert result.unwrap() == 17
    assert manager.tx.entered is True
    assert manager.tx.exited is True
    assert manager.tx.seen_exc is None


@pytest.mark.asyncio
async def test_run_result_in_tx_maps_raised_app_error_to_err_result() -> None:
    manager = _ManagerStub(tx=_TxScope())

    async def action() -> object:
        raise UnauthenticatedError()

    result = await run_result_in_tx(manager, action())

    assert result.is_err()
    assert isinstance(result.unwrap_err(), UnauthenticatedError)
    assert manager.tx.entered is True
    assert manager.tx.exited is True
    assert manager.tx.seen_exc is UnauthenticatedError


@pytest.mark.asyncio
async def test_run_result_in_tx_maps_err_result_and_rolls_back() -> None:
    manager = _ManagerStub(tx=_TxScope())

    async def action() -> object:
        return ResultImpl.err_app(UnauthenticatedError(), int)

    result = await run_result_in_tx(manager, action())

    assert result.is_err()
    assert isinstance(result.unwrap_err(), UnauthenticatedError)
    assert manager.tx.entered is True
    assert manager.tx.exited is True
    assert manager.tx.seen_exc is UnauthenticatedError
