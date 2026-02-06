from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import (
    AbstractAsyncContextManager,
    asynccontextmanager,
    suppress,
)
from dataclasses import dataclass

from redis.asyncio import Redis
from redis.asyncio.lock import Lock
from redis.exceptions import LockError

from backend.application.common.exceptions.auth import (
    RefreshTokenLockTimeoutError,
)
from backend.application.common.interfaces.ports.shared_lock import SharedLock

_LOCK_TTL_S: float = 10.0
_LOCK_WAIT_TIMEOUT_S: float = 1.0


@dataclass(slots=True)
class RedisSharedLock(SharedLock):
    client: Redis

    def __call__(
        self: RedisSharedLock, key: str
    ) -> AbstractAsyncContextManager[None]:
        return self._lock(key)

    @asynccontextmanager
    async def _lock(self: RedisSharedLock, key: str) -> AsyncIterator[None]:
        lock: Lock = self.client.lock(
            key,
            timeout=_LOCK_TTL_S,
            blocking_timeout=_LOCK_WAIT_TIMEOUT_S,
        )
        acquired: bool = await lock.acquire()
        if not acquired:
            raise RefreshTokenLockTimeoutError(
                "Failed to acquire refresh token lock"
            )
        try:
            yield None
        finally:
            if await lock.owned():
                with suppress(LockError):
                    await lock.release()
