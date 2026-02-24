from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import RowMapping

from backend.infrastructure.tools.msgspec_convert import convert_record


def map_one[T](row: RowMapping | None, record_type: type[T]) -> T | None:
    if row is None:
        return None
    return convert_record(dict(row), record_type)


def map_many[T](rows: Sequence[RowMapping], record_type: type[T]) -> list[T]:
    return [convert_record(dict(row), record_type) for row in rows]
