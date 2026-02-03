from __future__ import annotations

from uuid_utils.compat import UUID


def value_to_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    if isinstance(value, (bytes, bytearray)):
        return UUID(bytes=bytes(value))
    return UUID(str(value))
