from __future__ import annotations

from dataclasses import dataclass
from typing import Self

import pytest

from backend.application.common.exceptions.application import (
    AppError,
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
    tx_scopes: list[_TxScope]

    def transaction(self: Self, *, nested: bool = False) -> _TxScope:
        _ = nested
        scope = _TxScope()
        self.tx_scopes.append(scope)
        return scope


@pytest.mark.asyncio
async def test_run_result_in_tx_unwraps_ok_result() -> None:
    manager = _ManagerStub(tx_scopes=[])

    async def action() -> object:
        return ResultImpl.ok(17, UnauthenticatedError)

    result = await run_result_in_tx(manager, action_factory=action)

    assert result.is_ok()
    assert result.unwrap() == 17
    assert len(manager.tx_scopes) == 1
    assert manager.tx_scopes[0].entered is True
    assert manager.tx_scopes[0].exited is True
    assert manager.tx_scopes[0].seen_exc is None


@pytest.mark.asyncio
async def test_run_result_in_tx_maps_raised_app_error_to_err_result() -> None:
    manager = _ManagerStub(tx_scopes=[])

    async def action() -> object:
        raise UnauthenticatedError()

    result = await run_result_in_tx(manager, action_factory=action)

    assert result.is_err()
    assert isinstance(result.unwrap_err(), UnauthenticatedError)
    assert len(manager.tx_scopes) == 1
    assert manager.tx_scopes[0].entered is True
    assert manager.tx_scopes[0].exited is True
    assert manager.tx_scopes[0].seen_exc is UnauthenticatedError


@pytest.mark.asyncio
async def test_run_result_in_tx_maps_err_result_and_rolls_back() -> None:
    manager = _ManagerStub(tx_scopes=[])

    async def action() -> object:
        return ResultImpl.err_app(UnauthenticatedError(), int)

    result = await run_result_in_tx(manager, action_factory=action)

    assert result.is_err()
    assert isinstance(result.unwrap_err(), UnauthenticatedError)
    assert len(manager.tx_scopes) == 1
    assert manager.tx_scopes[0].entered is True
    assert manager.tx_scopes[0].exited is True
    assert manager.tx_scopes[0].seen_exc is UnauthenticatedError


@pytest.mark.asyncio
async def test_run_result_in_tx_retries_transient_error_and_eventually_succeeds() -> (
    None
):
    manager = _ManagerStub(tx_scopes=[])
    attempts = 0

    async def action() -> object:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return ResultImpl.err_app(
                AppError(
                    code="db.transient.deadlock_detected",
                    message="Temporary database error",
                ),
                int,
            )
        return ResultImpl.ok(42, AppError)

    result = await run_result_in_tx(
        manager,
        action_factory=action,
        max_attempts=2,
        backoff_base_s=0,
        backoff_jitter_s=0,
    )

    assert result.is_ok()
    assert result.unwrap() == 42
    assert attempts == 2
    assert len(manager.tx_scopes) == 2
    assert manager.tx_scopes[0].seen_exc is AppError
    assert manager.tx_scopes[1].seen_exc is None


@pytest.mark.asyncio
async def test_run_result_in_tx_does_not_retry_non_transient_error() -> None:
    manager = _ManagerStub(tx_scopes=[])
    attempts = 0

    async def action() -> object:
        nonlocal attempts
        attempts += 1
        return ResultImpl.err_app(
            AppError(code="internal.error", message="Internal server error"),
            int,
        )

    result = await run_result_in_tx(
        manager,
        action_factory=action,
        max_attempts=3,
        backoff_base_s=0,
        backoff_jitter_s=0,
    )

    assert result.is_err()
    assert result.unwrap_err().code == "internal.error"
    assert attempts == 1
    assert len(manager.tx_scopes) == 1


@pytest.mark.asyncio
async def test_run_result_in_tx_stops_retry_after_max_attempts() -> None:
    manager = _ManagerStub(tx_scopes=[])
    attempts = 0

    async def action() -> object:
        nonlocal attempts
        attempts += 1
        return ResultImpl.err_app(
            AppError(
                code="db.transient.serialization_failure",
                message="Temporary database error",
            ),
            int,
        )

    result = await run_result_in_tx(
        manager,
        action_factory=action,
        max_attempts=3,
        backoff_base_s=0,
        backoff_jitter_s=0,
    )

    assert result.is_err()
    assert result.unwrap_err().code == "db.transient.serialization_failure"
    assert attempts == 3
    assert len(manager.tx_scopes) == 3
