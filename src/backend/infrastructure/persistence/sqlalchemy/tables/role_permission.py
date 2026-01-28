from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid_utils.compat import UUID

from backend.infrastructure.persistence.sqlalchemy.tables.base import metadata
from backend.infrastructure.persistence.sqlalchemy.tables.permission import (
    permission_code_column,
)
from backend.infrastructure.persistence.sqlalchemy.tables.role import (
    role_id_column,
)
from backend.infrastructure.persistence.sqlalchemy.tables.users import (
    user_id_column,
)

role_permission_role_id_column: Column[UUID] = Column(
    "role_id",
    PG_UUID(as_uuid=True),
    ForeignKey(role_id_column, ondelete="CASCADE"),
    primary_key=True,
    nullable=False,
)

role_permission_code_column: Column[str] = Column(
    "permission_code",
    String(64),
    ForeignKey(permission_code_column, ondelete="CASCADE"),
    primary_key=True,
    nullable=False,
)

# TODO: Seed from ROLE_PERMISSIONS once a project seeding pattern is defined.
role_permissions_table: Table = Table(
    "role_permissions",
    metadata,
    role_permission_role_id_column,
    role_permission_code_column,
)

user_roles_user_id_column: Column[UUID] = Column(
    "user_id",
    PG_UUID(as_uuid=True),
    ForeignKey(user_id_column, ondelete="CASCADE"),
    primary_key=True,
    nullable=False,
)

user_roles_role_id_column: Column[UUID] = Column(
    "role_id",
    PG_UUID(as_uuid=True),
    ForeignKey(role_id_column, ondelete="CASCADE"),
    primary_key=True,
    nullable=False,
)


user_roles_table: Table = Table(
    "user_roles",
    metadata,
    user_roles_user_id_column,
    user_roles_role_id_column,
)
