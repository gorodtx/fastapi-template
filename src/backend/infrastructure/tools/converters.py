from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypeGuard

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.domain.core.value_objects.password import Password


class StrValueObjectCtor(Protocol):
    __name__: str

    def __call__(self, value: str) -> object: ...


class ConversionError(Exception): ...


class Converter(Protocol):
    def encode(self, value: object) -> object: ...

    def decode(self, value: object) -> object: ...


def _is_str(value: object) -> TypeGuard[str]:
    return isinstance(value, str)


@dataclass(frozen=True, slots=True)
class StrValueObjectConverter:
    vo_type: StrValueObjectCtor

    def encode(self, value: object) -> object:
        raw = getattr(value, "value", None)
        if not _is_str(raw):
            raise ConversionError(
                f"{self.vo_type.__name__}.value must be str, got {type(raw).__name__}"
            )
        return raw

    def decode(self, value: object) -> object:
        if not _is_str(value):
            raise ConversionError(f"Expected str, got {type(value).__name__}")
        return self.vo_type(value)


@dataclass(frozen=True, slots=True)
class StrEnumValueConverter[E: Enum]:
    enum_type: type[E]

    def encode(self, value: object) -> object:
        if not isinstance(value, self.enum_type):
            raise ConversionError(f"Expected {self.enum_type.__name__}, got {type(value).__name__}")
        raw = getattr(value, "value", None)
        if not _is_str(raw):
            raise ConversionError(
                f"{self.enum_type.__name__}.value must be str, got {type(raw).__name__}"
            )
        return raw

    def decode(self, value: object) -> object:
        if not _is_str(value):
            raise ConversionError(f"Expected str enum value, got {type(value).__name__}")
        try:
            return self.enum_type(value)
        except ValueError as exc:
            raise ConversionError(f"Unknown {self.enum_type.__name__} value: {value!r}") from exc


class ConverterRegistry:
    __slots__ = ("_by_type",)

    def __init__(self) -> None:
        self._by_type: dict[type[object], Converter] = {}

    def register(self, tp: type[object], conv: Converter) -> None:
        self._by_type[tp] = conv

    def _find(self, tp: type[object]) -> Converter | None:
        for base in tp.mro():
            conv = self._by_type.get(base)
            if conv is not None:
                return conv
        return None

    def encode(self, value: object) -> object:
        if value is None:
            return None
        conv = self._find(type(value))
        return value if conv is None else conv.encode(value)

    def decode[T](self, value: object, target_type: type[T]) -> T | None:
        if value is None:
            return None
        conv = self._find(target_type)
        if conv is None:
            if isinstance(value, target_type):
                return value
            raise ConversionError(f"Cannot decode {type(value).__name__} as {target_type.__name__}")
        decoded = conv.decode(value)
        if not isinstance(decoded, target_type):
            raise ConversionError(f"Decoded {type(decoded).__name__} is not {target_type.__name__}")
        return decoded


CONVERTERS = ConverterRegistry()


def register_domain_converters() -> None:
    CONVERTERS.register(Email, StrValueObjectConverter(Email))
    CONVERTERS.register(Login, StrValueObjectConverter(Login))
    CONVERTERS.register(Username, StrValueObjectConverter(Username))
    CONVERTERS.register(Password, StrValueObjectConverter(Password))
    CONVERTERS.register(SystemRole, StrEnumValueConverter(SystemRole))
