from __future__ import annotations

from collections.abc import Callable

from backend.application.common.exceptions.application import AppError, ConflictError
from backend.application.common.exceptions.storage import StorageError


def map_storage_error_to_app() -> Callable[[StorageError], AppError]:
    def mapper(error: StorageError) -> AppError:
        if error.code == "db.unique_violation":
            return ConflictError(error.message, detail=error.detail, meta=error.meta)
        return AppError(
            code=error.code,
            message=error.message,
            detail=error.detail,
            meta=error.meta,
        )

    return mapper
