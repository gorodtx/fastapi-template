from __future__ import annotations

from dataclasses import dataclass

from redis.asyncio import Redis

from backend.application.common.interfaces.ports.cache import StrCache


@dataclass(slots=True)
class RedisCache(StrCache):
    client: Redis

    async def get(self: RedisCache, key: str) -> str | None:
        value = await self.client.get(key)
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode("utf-8")
        if isinstance(value, str):
            return value
        raise TypeError(f"Unexpected cache value type: {type(value).__name__}")

    async def set(
        self: RedisCache, key: str, value: str, *, ttl_s: int | None = None
    ) -> None:
        await self.client.set(key, value, ex=ttl_s)

    async def delete(self: RedisCache, key: str) -> None:
        await self.client.delete(key)

    async def increment(self: RedisCache, key: str, *, delta: int = 1) -> int:
        return int(await self.client.incrby(key, delta))
