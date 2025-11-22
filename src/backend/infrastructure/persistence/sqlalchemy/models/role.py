from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import mapper_registry, metadata

if TYPE_CHECKING:
    from sqlalchemy.orm import InstrumentedAttribute


roles_table = Table(
    "roles",
    metadata,
    Column("id", PG_UUID(as_uuid=True), primary_key=True, nullable=False),
    Column("name", String(16), nullable=False),
    Column("description", String(255), nullable=True),
    UniqueConstraint("name"),
)


class RoleModel:
    if TYPE_CHECKING:
        id: InstrumentedAttribute[uuid.UUID]

    def __init__(
        self,
        *,
        id: uuid.UUID,
        name: str,
        description: str | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description

    def __repr__(self) -> str:
        return f"RoleModel(id={self.id!r}, name={self.name!r})"


mapper_registry.map_imperatively(RoleModel, roles_table)
