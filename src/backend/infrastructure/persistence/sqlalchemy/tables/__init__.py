from __future__ import annotations

from backend.infrastructure.persistence.sqlalchemy.tables.base import (
    NAMING_CONVENTION,
    mapper_registry,
    metadata,
)
from backend.infrastructure.persistence.sqlalchemy.tables.permission import permissions_table
from backend.infrastructure.persistence.sqlalchemy.tables.role import roles_table
from backend.infrastructure.persistence.sqlalchemy.tables.role_permission import (
    role_permissions_table,
    user_roles_table,
)
from backend.infrastructure.persistence.sqlalchemy.tables.users import users_table

__all__ = [
    "NAMING_CONVENTION",
    "mapper_registry",
    "metadata",
    "permissions_table",
    "role_permissions_table",
    "roles_table",
    "user_roles_table",
    "users_table",
]
