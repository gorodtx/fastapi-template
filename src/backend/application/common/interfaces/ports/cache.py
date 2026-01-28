from __future__ import annotations

from typing import Protocol


class StrCache(Protocol):
    async def get(self: StrCache, key: str) -> str | None: ...

    async def set(
        self: StrCache, key: str, value: str, *, ttl_s: int | None = None
    ) -> None: ...

    async def delete(self: StrCache, key: str) -> None: ...

    async def increment(
        self: StrCache, key: str, *, delta: int = 1
    ) -> int: ...
