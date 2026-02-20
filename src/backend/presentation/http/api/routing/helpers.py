from __future__ import annotations

import logging
from collections.abc import Awaitable

from backend.application.common.exceptions.application import AppError
from backend.application.handlers.result import Result

_LOGGER = logging.getLogger(__name__)


async def run_best_effort(
    action: Awaitable[None],
    /,
    *,
    effect: str,
) -> None:
    try:
        await action
    except Exception:
        _LOGGER.exception("Post-commit side effect failed: %s", effect)


async def unwrap_result[T](
    action: Awaitable[Result[T, AppError]],
) -> T:
    return (await action).unwrap()
