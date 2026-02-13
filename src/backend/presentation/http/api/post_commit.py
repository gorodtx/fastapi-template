from __future__ import annotations

import logging
from collections.abc import Awaitable

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
