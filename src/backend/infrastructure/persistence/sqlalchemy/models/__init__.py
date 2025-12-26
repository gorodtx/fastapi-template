from __future__ import annotations

from backend.infrastructure.persistence.sqlalchemy.models.base import (
    NAMING_CONVENTION,
    mapper_registry,
    metadata,
)
from backend.infrastructure.persistence.sqlalchemy.models.role import roles_table
from backend.infrastructure.persistence.sqlalchemy.models.role_permission import (
    role_permissions_table,
    user_roles_table,
)
from backend.infrastructure.persistence.sqlalchemy.models.users import users_table

__all__ = [
    "NAMING_CONVENTION",
    "mapper_registry",
    "metadata",
    "role_permissions_table",
    "roles_table",
    "user_roles_table",
    "users_table",
]
