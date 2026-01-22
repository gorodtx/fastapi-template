from __future__ import annotations

from sqlalchemy import Column, Enum, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid_utils.compat import UUID

from backend.domain.core.constants.rbac import SystemRole
from backend.infrastructure.persistence.sqlalchemy.tables.base import metadata

role_id_column: Column[UUID] = Column(
    "id",
    PG_UUID(as_uuid=True),
    primary_key=True,
    nullable=False,
)

role_code_column: Column[SystemRole] = Column(
    "code",
    Enum(SystemRole, native_enum=False),
    nullable=False,
)

role_description_column: Column[str] = Column(
    "description",
    String(255),
    nullable=True,
)

roles_table = Table(
    "roles",
    metadata,
    role_id_column,
    role_code_column,
    role_description_column,
    UniqueConstraint(role_code_column),
)
