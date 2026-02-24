from __future__ import annotations

import asyncio
import secrets
from collections.abc import Awaitable, Callable

from backend.application.common.exceptions.application import AppError
from backend.application.common.interfaces.ports.persistence.manager import (
    TransactionManager,
)
from backend.application.handlers.result import Result, ResultImpl

_RETRYABLE_ERROR_PREFIX: str = "db.transient."
_DEFAULT_MAX_ATTEMPTS: int = 3
_DEFAULT_BACKOFF_BASE_S: float = 0.05
_DEFAULT_BACKOFF_JITTER_S: float = 0.02


async def run_result_in_tx[T](
    manager: TransactionManager,
    action_factory: Callable[[], Awaitable[Result[T, AppError]]],
    *,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    backoff_base_s: float = _DEFAULT_BACKOFF_BASE_S,
    backoff_jitter_s: float = _DEFAULT_BACKOFF_JITTER_S,
) -> Result[T, AppError]:
    if max_attempts <= 0:
        raise ValueError("max_attempts must be greater than zero")
    if backoff_base_s < 0:
        raise ValueError("backoff_base_s must be non-negative")
    if backoff_jitter_s < 0:
        raise ValueError("backoff_jitter_s must be non-negative")

    for attempt in range(1, max_attempts + 1):
        try:
            async with manager.transaction():
                value = (await action_factory()).unwrap()
                return ResultImpl.ok(value)
        except AppError as exc:
            if _is_retryable_transient_error(exc) and attempt < max_attempts:
                await asyncio.sleep(
                    _compute_retry_delay(
                        attempt=attempt,
                        backoff_base_s=backoff_base_s,
                        backoff_jitter_s=backoff_jitter_s,
                    )
                )
                continue
            return ResultImpl.err_app(exc)

    raise RuntimeError("Transactional action exhausted without returning")


def _is_retryable_transient_error(exc: AppError) -> bool:
    return exc.code.startswith(_RETRYABLE_ERROR_PREFIX)


def _compute_retry_delay(
    *, attempt: int, backoff_base_s: float, backoff_jitter_s: float
) -> float:
    exponential = backoff_base_s * (2 ** (attempt - 1))
    if backoff_jitter_s == 0:
        return exponential
    jitter_factor = secrets.randbelow(1_000_000) / 1_000_000
    jitter = backoff_jitter_s * jitter_factor
    return exponential + jitter
