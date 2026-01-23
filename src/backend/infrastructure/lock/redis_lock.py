from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass

from redis.asyncio import Redis
from redis.asyncio.lock import Lock

from backend.application.common.interfaces.ports.shared_lock import SharedLock


@dataclass(slots=True)
class RedisSharedLock(SharedLock):
    client: Redis

    def __call__(self, key: str) -> AbstractAsyncContextManager[None]:
        return self._lock(key)

    @asynccontextmanager
    async def _lock(self, key: str) -> AsyncIterator[None]:
        lock: Lock = self.client.lock(key)
        await lock.acquire()
        try:
            yield None
        finally:
            await lock.release()
