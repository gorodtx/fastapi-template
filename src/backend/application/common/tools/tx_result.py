from __future__ import annotations

from collections.abc import Awaitable, Callable

from backend.application.common.exceptions.application import AppError
from backend.application.common.interfaces.ports.persistence.manager import (
    TransactionManager,
)
from backend.application.handlers.result import Result, ResultImpl


async def run_in_tx[T](
    manager: TransactionManager,
    action: Callable[[], Awaitable[T]],
    value_type: type[T],
) -> Result[T, AppError]:
    try:
        async with manager.transaction():
            value = await action()
            return ResultImpl.ok(value, AppError)
    except AppError as exc:
        return ResultImpl.err_app(exc, value_type)
