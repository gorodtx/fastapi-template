from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Protocol

from sqlalchemy import MetaData
from sqlalchemy.sql.schema import Constraint, PrimaryKeyConstraint, UniqueConstraint


class ConstraintMessageProvider(Protocol):
    def resolve(self, constraint: str) -> tuple[str | None, str]: ...


_GENERIC_UNIQUE_MESSAGE: Final[str] = "Unique constraint violated."


def build_constraint_index(
    metadata: MetaData,
) -> dict[str, tuple[str, ...]]:
    index: dict[str, tuple[str, ...]] = {}

    for table in metadata.tables.values():
        for constraint in table.constraints:
            name = constraint.name
            if not isinstance(name, str):
                continue

            columns = _extract_constraint_columns(constraint)
            if not columns:
                continue

            index[name] = columns

    return index


def _extract_constraint_columns(
    constraint: Constraint,
) -> tuple[str, ...] | None:
    if not isinstance(constraint, (UniqueConstraint, PrimaryKeyConstraint)):
        return None

    column_source = constraint.columns
    if not column_source:
        return None

    names = tuple(column.name for column in column_source)
    return names or None


@dataclass(frozen=True, slots=True)
class MetaDataConstraintMessageProvider:
    _index: Mapping[str, tuple[str, ...]]

    def resolve(self, constraint: str) -> tuple[str | None, str]:
        columns = self._index.get(constraint)

        if not columns:
            return None, _GENERIC_UNIQUE_MESSAGE

        if len(columns) == 1:
            field = columns[0]
            return field, f"Field '{field}' must be unique."

        human = " + ".join(f"'{c}'" for c in columns)
        return None, f"Combination {human} must be unique."
