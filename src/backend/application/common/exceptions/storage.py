from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StorageError(Exception):
    code: str
    message: str
    detail: str | None = None
    meta: dict[str, object] | None = None


class NotFoundStorageError(StorageError):
    def __init__(
        self: NotFoundStorageError,
        *,
        code: str,
        message: str,
        detail: str | None = None,
        meta: dict[str, object] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, detail=detail, meta=meta)
