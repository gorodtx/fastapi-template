from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol


class SharedLock(Protocol):
    def __call__(
        self: SharedLock, key: str
    ) -> AbstractAsyncContextManager[None]: ...
