from __future__ import annotations

from typing import Protocol


class PasswordHasherPort(Protocol):
    async def hash(self, raw_password: str) -> str: ...

    async def verify(self, raw_password: str, hashed_password: str) -> bool: ...

    async def needs_rehash(self, hashed_password: str) -> bool: ...
