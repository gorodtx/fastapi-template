from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, TypeGuard, runtime_checkable

from backend.application.common.interfaces.ports.serialization import DTOCodec
from backend.infrastructure.tools.msgspec_tools import (
    convert_from,
    convert_to,
    msgpack_decoder,
    msgpack_encoder,
    msgspec_decoder,
    msgspec_encoder,
)


def _normalize_mapping(
    raw: Mapping[object, object],
    *,
    exclude_none: bool,
    exclude: set[str],
) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in raw.items():
        key_str = str(key)
        if key_str in exclude:
            continue
        if exclude_none and value is None:
            continue
        out[key_str] = value
    return out


def _is_mapping(value: object) -> TypeGuard[Mapping[object, object]]:
    return isinstance(value, Mapping)


@runtime_checkable
class _SupportsAsMapping(Protocol):
    def as_mapping(
        self: _SupportsAsMapping, *, exclude_none: bool, exclude: set[str]
    ) -> Mapping[object, object]: ...


class MsgspecDTOCodec(DTOCodec):
    def to_mapping(
        self: MsgspecDTOCodec,
        obj: object,
        *,
        exclude_none: bool = False,
        exclude: set[str] | None = None,
    ) -> Mapping[str, object]:
        ex = exclude or set()

        if isinstance(obj, _SupportsAsMapping):
            raw = obj.as_mapping(exclude_none=False, exclude=ex)
            if not _is_mapping(raw):
                raise TypeError("as_mapping must return a mapping")
            return _normalize_mapping(
                raw, exclude_none=exclude_none, exclude=ex
            )

        builtins: object = convert_from(obj)

        if _is_mapping(builtins):
            return _normalize_mapping(
                builtins, exclude_none=exclude_none, exclude=ex
            )

        return {"value": builtins}

    def to_string(
        self: MsgspecDTOCodec,
        obj: object,
        *,
        exclude_none: bool = False,
        exclude: set[str] | None = None,
    ) -> str:
        if exclude_none or exclude:
            return msgspec_encoder(
                self.to_mapping(
                    obj, exclude_none=exclude_none, exclude=exclude
                )
            )
        return msgspec_encoder(obj)

    def to_bytes(
        self: MsgspecDTOCodec,
        obj: object,
        *,
        exclude_none: bool = False,
        exclude: set[str] | None = None,
    ) -> bytes:
        if exclude_none or exclude:
            return msgpack_encoder(
                self.to_mapping(
                    obj, exclude_none=exclude_none, exclude=exclude
                )
            )
        return msgpack_encoder(obj)

    def from_mapping[T](
        self: MsgspecDTOCodec,
        cls: type[T],
        value: Mapping[str, object],
        *,
        strict: bool = False,
    ) -> T:
        return convert_to(cls, value, strict=strict)

    def from_string[T](
        self: MsgspecDTOCodec,
        cls: type[T],
        value: str,
        *,
        strict: bool = False,
    ) -> T:
        data = msgspec_decoder(value, strict=strict)
        return convert_to(cls, data, strict=strict)

    def from_bytes[T](
        self: MsgspecDTOCodec,
        cls: type[T],
        value: bytes,
        *,
        strict: bool = False,
    ) -> T:
        data = msgpack_decoder(value, strict=strict)
        return convert_to(cls, data, strict=strict)
