from __future__ import annotations

import inspect
import uuid
from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Final, Literal

import msgspec

DEFAULT_CONVERT_TO_TYPES: Final[tuple[type, ...]] = (
    bytes,
    bytearray,
    datetime,
    time,
    date,
    timedelta,
    uuid.UUID,
    Decimal,
)
DEFAULT_CONVERT_FROM_TYPES: Final[tuple[type, ...]] = (*DEFAULT_CONVERT_TO_TYPES, memoryview)


def convert_to[T](cls: type[T], value: object, *, strict: bool = False) -> T:
    return msgspec.convert(
        value,
        cls,
        strict=strict,
        builtin_types=DEFAULT_CONVERT_TO_TYPES,
    )


def convert_from(value: object) -> object:
    return msgspec.to_builtins(value, builtin_types=DEFAULT_CONVERT_FROM_TYPES)


def msgpack_encoder(
    obj: object, *, order: Literal["deterministic", "sorted"] | None = None
) -> bytes:
    return msgspec.msgpack.encode(obj, order=order)


def msgpack_decoder(obj: bytes, *, strict: bool = False) -> object:
    return msgspec.msgpack.decode(obj, strict=strict)


def msgspec_encoder(obj: object, *, order: Literal["deterministic", "sorted"] | None = None) -> str:
    return msgspec.json.encode(obj, order=order).decode("utf-8")


def msgspec_decoder(obj: str, *, strict: bool = False) -> object:
    return msgspec.json.decode(obj, strict=strict)


class ClosableProxy:
    __slots__ = ("_close_fn", "_target")

    def __init__(self, target: object, close_fn: Callable[[], object]) -> None:
        self._target = target
        self._close_fn = close_fn

    async def close(self) -> None:
        if inspect.iscoroutinefunction(self._close_fn):
            await self._close_fn()
        else:
            res = self._close_fn()
            if inspect.isawaitable(res):
                await res

    def __getattr__(self, key: str) -> object:
        return getattr(self._target, key)

    def __repr__(self) -> str:
        return f"{self._target!r}"
