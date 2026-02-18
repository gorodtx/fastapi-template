from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass

from argon2 import PasswordHasher, Type
from argon2.exceptions import (
    HashingError,
    InvalidHashError,
    VerifyMismatchError,
)

from backend.domain.core.policies.identity import (
    MAX_PASSWORD_LENGTH,
    normalize_password,
)


@dataclass(frozen=True, slots=True)
class Argon2Config:
    time_cost: int = 3
    memory_cost_kib: int = 65536
    parallelism: int = 4
    hash_len: int = 32
    salt_len: int = 16


class Argon2PasswordHasher:
    def __init__(
        self: Argon2PasswordHasher, *, cfg: Argon2Config | None = None
    ) -> None:
        config = cfg or Argon2Config()
        self._hasher = PasswordHasher(
            time_cost=config.time_cost,
            memory_cost=config.memory_cost_kib,
            parallelism=config.parallelism,
            hash_len=config.hash_len,
            salt_len=config.salt_len,
            type=Type.ID,
        )

    def _normalize(self: Argon2PasswordHasher, raw_password: str) -> str:
        return normalize_password(raw_password)

    def _too_long(self: Argon2PasswordHasher, normalized: str) -> bool:
        return len(normalized) > MAX_PASSWORD_LENGTH

    async def hash(self: Argon2PasswordHasher, raw_password: str) -> str:
        normalized = self._normalize(raw_password)
        if self._too_long(normalized):
            raise ValueError(
                f"Password too long (max {MAX_PASSWORD_LENGTH} characters)"
            )
        try:
            return await _run_sync1(self._hasher.hash, normalized)
        except HashingError as e:
            raise RuntimeError(f"Password hashing failed: {e}") from e

    async def verify(
        self: Argon2PasswordHasher, raw_password: str, hashed_password: str
    ) -> bool:
        normalized = self._normalize(raw_password)
        if self._too_long(normalized):
            return False
        try:
            return await _run_sync2(
                self._hasher.verify, hashed_password, normalized
            )
        except VerifyMismatchError:
            return False
        except InvalidHashError as e:
            raise ValueError(f"Invalid hash format: {e}") from e

    async def needs_rehash(
        self: Argon2PasswordHasher, hashed_password: str
    ) -> bool:
        def _compute() -> bool:
            try:
                return bool(self._hasher.check_needs_rehash(hashed_password))
            except InvalidHashError:
                return True

        return await _run_sync0(_compute)


async def _run_sync0[T](func: Callable[[], T]) -> T:
    return await asyncio.to_thread(func)


async def _run_sync1[A, T](func: Callable[[A], T], arg: A) -> T:
    return await asyncio.to_thread(func, arg)


async def _run_sync2[A, B, T](
    func: Callable[[A, B], T], arg1: A, arg2: B
) -> T:
    return await asyncio.to_thread(func, arg1, arg2)
