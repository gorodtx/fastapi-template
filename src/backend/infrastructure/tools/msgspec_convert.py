from __future__ import annotations

import inspect
import uuid
from collections.abc import Callable, Mapping
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Final, Literal, Protocol, runtime_checkable

import msgspec
from uuid_utils.compat import UUID

from backend.infrastructure.tools.domain_converters import (
    CONVERTERS,
    ConversionError,
)

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
DEFAULT_CONVERT_FROM_TYPES: Final[tuple[type, ...]] = (
    *DEFAULT_CONVERT_TO_TYPES,
    memoryview,
)


@runtime_checkable
class _Fallback(Protocol):
    def __call__(self: _Fallback, name: str) -> object: ...


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


def msgspec_encoder(
    obj: object, *, order: Literal["deterministic", "sorted"] | None = None
) -> str:
    return msgspec.json.encode(obj, order=order).decode("utf-8")


def msgspec_decoder(obj: str, *, strict: bool = False) -> object:
    return msgspec.json.decode(obj, strict=strict)


def _row_dec_hook(tp: type[object], obj: object) -> object:
    if tp is UUID:
        if isinstance(obj, UUID):
            return obj
        return UUID(str(obj))
    if tp is bool:
        if isinstance(obj, bool):
            return obj
        return bool(obj)
    if tp is str:
        if isinstance(obj, str):
            return obj
        encoded = CONVERTERS.encode(obj)
        if not isinstance(encoded, str):
            raise TypeError("Expected str")
        return encoded
    try:
        decoded = CONVERTERS.decode(obj, tp)
    except ConversionError as exc:
        raise NotImplementedError from exc
    if decoded is None:
        raise TypeError(f"Expected {tp.__name__}")
    return decoded


def convert_record[T](row: Mapping[str, object], record_type: type[T]) -> T:
    return msgspec.convert(
        dict(row),
        record_type,
        strict=True,
        dec_hook=_row_dec_hook,
    )


class ClosableProxy:
    __slots__: tuple[str, ...] = ("_close_fn", "_target")

    def __init__(
        self: ClosableProxy, target: object, close_fn: Callable[[], object]
    ) -> None:
        self._target = target
        self._close_fn = close_fn

    async def close(self: ClosableProxy) -> None:
        if inspect.iscoroutinefunction(self._close_fn):
            await self._close_fn()
        else:
            res = self._close_fn()
            if inspect.isawaitable(res):
                await res

    def __getattr__(self: ClosableProxy, key: str) -> object:
        try:
            return self._target.__getattribute__(key)
        except AttributeError:
            try:
                fallback = object.__getattribute__(self._target, "__getattr__")
            except AttributeError:
                raise
            if isinstance(fallback, _Fallback):
                return fallback(key)
            raise

    def __repr__(self: ClosableProxy) -> str:
        return f"{self._target!r}"
