from __future__ import annotations

from typing import Protocol


class PasswordHasherPort(Protocol):
    async def hash(self: PasswordHasherPort, raw_password: str) -> str: ...

    async def verify(
        self: PasswordHasherPort, raw_password: str, hashed_password: str
    ) -> bool: ...

    async def needs_rehash(
        self: PasswordHasherPort, hashed_password: str
    ) -> bool: ...
