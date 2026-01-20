from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from typing import Final

from argon2 import PasswordHasher, Type
from argon2.exceptions import HashingError, InvalidHashError, VerifyMismatchError

from backend.application.common.tools.password_validator import (
    MAX_PASSWORD_LENGTH,
    normalize_password,
)

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

    def _normalize_and_guard(self, raw_password: str) -> str:
        normalized = normalize_password(raw_password)

        # Guard against excessively long inputs (DoS). Do not truncate silently.
        if len(normalized) > MAX_PASSWORD_LENGTH:
            raise ValueError(f"Password too long (max {MAX_PASSWORD_LENGTH} characters)")

        return normalized

    async def hash(self, raw_password: str) -> str:
        normalized = self._normalize_and_guard(raw_password)
        try:
            return await _run_sync1(self._hasher.hash, normalized)
        except HashingError as e:
            raise RuntimeError(f"Password hashing failed: {e}") from e

    async def verify(self, raw_password: str, hashed_password: str) -> bool:
        normalized = self._normalize_and_guard(raw_password)
        try:
            return await _run_sync2(self._hasher.verify, hashed_password, normalized)
        except VerifyMismatchError:
            return False
        except InvalidHashError as e:
            raise ValueError(f"Invalid hash format: {e}") from e

    async def needs_rehash(self, hashed_password: str) -> bool:
        def _compute() -> bool:
            try:
                pattern: re.Pattern[str] = re.compile(
                    r"\$(argon2(?:id|i|d))\$v=(\d+)\$m=(\d+),t=(\d+),p=(\d+)\$"
                )
                match = pattern.match(hashed_password)
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

        return await _run_sync0(_compute)


async def _run_sync0[T](func: Callable[[], T]) -> T:
    return await asyncio.to_thread(func)


async def _run_sync1[A, T](func: Callable[[A], T], arg: A) -> T:
    return await asyncio.to_thread(func, arg)


async def _run_sync2[A, B, T](func: Callable[[A, B], T], arg1: A, arg2: B) -> T:
    return await asyncio.to_thread(func, arg1, arg2)
