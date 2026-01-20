from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps

from sqlalchemy.exc import DBAPIError, IntegrityError

from backend.application.common.exceptions.storage import StorageError
from backend.application.handlers.result import Result, ResultImpl
from backend.infrastructure.errors.sqlalchemy_errors import map_dbapi_error, map_integrity_error


def _default_map_exc(exc: Exception) -> StorageError:
    if isinstance(exc, StorageError):
        return exc
    if isinstance(exc, IntegrityError):
        return map_integrity_error(exc)
    if isinstance(exc, DBAPIError):
        return map_dbapi_error(exc)
    return StorageError(
        code="infra.unexpected",
        message="Unexpected infrastructure error",
        detail=str(exc),
    )


def as_result[T, A1, A2](
    *,
    map_err: Callable[[Exception], StorageError] | None = None,
) -> Callable[
    [Callable[[A1, A2], Awaitable[T]]], Callable[[A1, A2], Awaitable[Result[T, StorageError]]]
]:
    mapper = map_err or _default_map_exc

    def decorator(
        fn: Callable[[A1, A2], Awaitable[T]],
    ) -> Callable[[A1, A2], Awaitable[Result[T, StorageError]]]:
        @wraps(fn)
        async def wrapper(a1: A1, a2: A2) -> Result[T, StorageError]:
            try:
                return ResultImpl.ok(await fn(a1, a2))
            except Exception as exc:
                if isinstance(exc, StorageError):
                    return ResultImpl.err(exc)
                return ResultImpl.err(mapper(exc))

        return wrapper

    return decorator
