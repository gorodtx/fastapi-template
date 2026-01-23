from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, Self


class DTOCodec(Protocol):
    def to_mapping(
        self,
        obj: object,
        *,
        exclude_none: bool = False,
        exclude: set[str] | None = None,
    ) -> Mapping[str, object]: ...

    def to_string(
        self,
        obj: object,
        *,
        exclude_none: bool = False,
        exclude: set[str] | None = None,
    ) -> str: ...

    def to_bytes(
        self,
        obj: object,
        *,
        exclude_none: bool = False,
        exclude: set[str] | None = None,
    ) -> bytes: ...

    def from_mapping[T](
        self, cls: type[T], value: Mapping[str, object], *, strict: bool = False
    ) -> T: ...

    def from_string[T](self, cls: type[T], value: str, *, strict: bool = False) -> T: ...
    def from_bytes[T](self, cls: type[T], value: bytes, *, strict: bool = False) -> T: ...


class Serializable(Protocol):
    def as_mapping(
        self,
        *,
        exclude_none: bool = False,
        exclude: set[str] | None = None,
    ) -> Mapping[str, object]: ...


class Deserializable(Protocol):
    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> Self: ...


class DTO(Serializable, Deserializable, Protocol): ...
