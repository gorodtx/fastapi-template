from __future__ import annotations

from collections.abc import Mapping

import msgspec
from uuid_utils.compat import UUID

from backend.domain.core.exceptions.serialization import (
    DomainSerializationError,
)
from backend.infrastructure.tools.serialization import (
    decode_value,
    encode_str,
)


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
        return encode_str(obj)
    try:
        decoded = decode_value(obj, tp)
    except DomainSerializationError as exc:
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
