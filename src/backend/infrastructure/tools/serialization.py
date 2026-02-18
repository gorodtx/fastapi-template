from __future__ import annotations

from collections.abc import Callable
from typing import Final

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.exceptions.serialization import (
    DomainSerializationError,
)

type Encoder = Callable[[object], str]
type Decoder = Callable[[object], object]


def _encode_system_role(value: object) -> str:
    if isinstance(value, SystemRole):
        return value.value
    raise DomainSerializationError(
        f"Expected {SystemRole.__name__}, got {type(value).__name__}"
    )


def _decode_system_role(value: object) -> SystemRole:
    if isinstance(value, SystemRole):
        return value
    if not isinstance(value, str):
        raise DomainSerializationError(
            f"Expected str enum value, got {type(value).__name__}"
        )
    try:
        return SystemRole(value)
    except ValueError as exc:
        raise DomainSerializationError(
            f"Unknown {SystemRole.__name__} value: {value!r}"
        ) from exc


_CONVERTERS: Final[dict[type[object], tuple[Encoder, Decoder]]] = {
    SystemRole: (_encode_system_role, _decode_system_role)
}


def encode_str(value: object) -> str:
    if isinstance(value, str):
        return value
    for target_type, (encode, _decode) in _CONVERTERS.items():
        if isinstance(value, target_type):
            return encode(value)
    raise DomainSerializationError(f"Expected str, got {type(value).__name__}")


def decode_value(value: object, target_type: type[object]) -> object:
    if value is None:
        return None
    converter = _CONVERTERS.get(target_type)
    if converter is None:
        if isinstance(value, target_type):
            return value
        raise DomainSerializationError(
            f"Cannot decode {type(value).__name__} as {target_type.__name__}"
        )
    _encode, decode = converter
    decoded = decode(value)
    if not isinstance(decoded, target_type):
        raise DomainSerializationError(
            f"Decoded {type(decoded).__name__} is not {target_type.__name__}"
        )
    return decoded
