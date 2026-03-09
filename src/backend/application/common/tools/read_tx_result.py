from __future__ import annotations

from collections.abc import Awaitable, Callable

from backend.application.common.exceptions.application import AppError
from backend.application.common.interfaces.ports.persistence.manager import (
    TransactionManager,
)
from backend.application.handlers.result import Result, ResultImpl


async def run_result_in_read_tx[T](
    manager: TransactionManager,
    action_factory: Callable[[], Awaitable[Result[T, AppError]]],
) -> Result[T, AppError]:
    """
    Ensure DB work for read-use-cases lives within an explicit transaction scope.

    Important: when action returns Err, we unwrap() to raise AppError and force a
    rollback so the session doesn't stay in a broken transactional state after a
    DB error.
    """
    try:
        async with manager.transaction():
            value = (await action_factory()).unwrap()
            return ResultImpl.ok(value)
    except AppError as exc:
        return ResultImpl.err_app(exc)
