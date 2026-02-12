from __future__ import annotations

from collections.abc import Awaitable

from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.common.exceptions.application import AppError
from backend.application.handlers.result import Result


async def run_write_in_tx[T](
    session: AsyncSession,
    action: Awaitable[Result[T, AppError]],
) -> T:
    async with session.begin():
        result = await action
        return result.unwrap()
