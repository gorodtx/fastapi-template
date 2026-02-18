from __future__ import annotations

from collections.abc import Awaitable

from backend.application.common.exceptions.application import AppError
from backend.application.common.interfaces.ports.persistence.manager import (
    TransactionManager,
)
from backend.application.handlers.result import Result, ResultImpl


async def run_result_in_tx[T](
    manager: TransactionManager,
    action: Awaitable[Result[T, AppError]],
) -> Result[T, AppError]:
    try:
        async with manager.transaction():
            value = (await action).unwrap()
            return ResultImpl.ok(value)
    except AppError as exc:
        return ResultImpl.err_app(exc)
