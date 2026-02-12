from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypeGuard

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.exceptions.serialization import (
    DomainSerializationError,
)


class Converter(Protocol):
    def encode(self: Converter, value: object) -> object: ...

    def decode(self: Converter, value: object) -> object: ...


def _is_str(value: object) -> TypeGuard[str]:
    return isinstance(value, str)


@dataclass(frozen=True, slots=True)
class StrEnumValueConverter:
    enum_type: type[Enum]

    def encode(self: StrEnumValueConverter, value: object) -> object:
        if not isinstance(value, self.enum_type):
            raise DomainSerializationError(
                f"Expected {self.enum_type.__name__}, got {type(value).__name__}"
            )
        raw = value.value
        if not _is_str(raw):
            raise DomainSerializationError(
                f"{self.enum_type.__name__}.value must be str, got {type(raw).__name__}"
            )
        return raw

    def decode(self: StrEnumValueConverter, value: object) -> object:
        if not _is_str(value):
            raise DomainSerializationError(
                f"Expected str enum value, got {type(value).__name__}"
            )
        try:
            return self.enum_type(value)
        except ValueError as exc:
            raise DomainSerializationError(
                f"Unknown {self.enum_type.__name__} value: {value!r}"
            ) from exc


class ConverterRegistry:
    __slots__: tuple[str, ...] = ("_by_type",)

    def __init__(self: ConverterRegistry) -> None:
        self._by_type: dict[type[object], Converter] = {}

    def register(
        self: ConverterRegistry, tp: type[object], conv: Converter
    ) -> None:
        self._by_type[tp] = conv

    def _find(self: ConverterRegistry, tp: type[object]) -> Converter | None:
        for base in tp.mro():
            conv = self._by_type.get(base)
            if conv is not None:
                return conv
        return None

    def encode(self: ConverterRegistry, value: object) -> object:
        if value is None:
            return None
        conv = self._find(type(value))
        return value if conv is None else conv.encode(value)

    def decode(
        self: ConverterRegistry, value: object, target_type: type[object]
    ) -> object:
        if value is None:
            return None
        conv = self._find(target_type)
        if conv is None:
            if isinstance(value, target_type):
                return value
            raise DomainSerializationError(
                f"Cannot decode {type(value).__name__} as {target_type.__name__}"
            )
        decoded = conv.decode(value)
        if not isinstance(decoded, target_type):
            raise DomainSerializationError(
                f"Decoded {type(decoded).__name__} is not {target_type.__name__}"
            )
        return decoded


CONVERTERS: ConverterRegistry = ConverterRegistry()


def encode_str(value: object) -> str:
    encoded = CONVERTERS.encode(value)
    if not isinstance(encoded, str):
        raise DomainSerializationError(
            f"Expected str, got {type(encoded).__name__}"
        )
    return encoded


def decode_value(value: object, target_type: type[object]) -> object:
    return CONVERTERS.decode(value, target_type)


def decode_system_role(value: object) -> SystemRole:
    decoded = CONVERTERS.decode(value, SystemRole)
    if not isinstance(decoded, SystemRole):
        raise DomainSerializationError(
            f"Decoded {type(decoded).__name__} is not SystemRole"
        )
    return decoded


def register_domain_converters() -> None:
    CONVERTERS.register(SystemRole, StrEnumValueConverter(SystemRole))
