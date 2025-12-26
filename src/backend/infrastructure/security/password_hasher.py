from __future__ import annotations

import re
from typing import Final

from argon2 import PasswordHasher, Type
from argon2.exceptions import HashingError, InvalidHashError, VerifyMismatchError

ARGON2_TIME_COST: Final[int] = 3
ARGON2_MEMORY_COST: Final[int] = 65536
ARGON2_PARALLELISM: Final[int] = 4
ARGON2_HASH_LEN: Final[int] = 32
ARGON2_SALT_LEN: Final[int] = 16

MIN_MEMORY_COST: Final[int] = 19456


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN,
            salt_len=ARGON2_SALT_LEN,
            type=Type.ID,
        )

    async def hash(self, raw_password: str) -> str:
        try:
            return self._hasher.hash(raw_password)
        except HashingError as e:
            raise RuntimeError(f"Password hashing failed: {e}") from e

    async def verify(self, raw_password: str, hashed: str) -> bool:
        try:
            self._hasher.verify(hashed, raw_password)
            return True
        except VerifyMismatchError:
            return False
        except InvalidHashError as e:
            raise ValueError(f"Invalid hash format: {e}") from e

    async def needs_rehash(self, hashed: str) -> bool:
        try:
            pattern: re.Pattern[str] = re.compile(
                r"\$(argon2(?:id|i|d))\$v=(\d+)\$m=(\d+),t=(\d+),p=(\d+)\$"
            )
            match = pattern.match(hashed)
            if match is None:
                return True

            algo: str = match.group(1)
            memory_raw: str = match.group(3)
            time_cost_raw: str = match.group(4)

            memory_cost = int(memory_raw)
            time_cost = int(time_cost_raw)

            if algo != "argon2id":
                return True
            if memory_cost < MIN_MEMORY_COST:
                return True
            return time_cost < ARGON2_TIME_COST

        except (ValueError, AttributeError):
            return True
