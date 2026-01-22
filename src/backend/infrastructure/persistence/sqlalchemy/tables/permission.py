from __future__ import annotations

from sqlalchemy import Column, String, Table

from backend.infrastructure.persistence.sqlalchemy.tables.base import metadata

permission_code_column: Column[str] = Column(
    "code",
    String(64),
    primary_key=True,
    nullable=False,
)

permission_description_column: Column[str] = Column(
    "description",
    String(255),
    nullable=True,
)

permissions_table = Table(
    "permissions",
    metadata,
    permission_code_column,
    permission_description_column,
)
