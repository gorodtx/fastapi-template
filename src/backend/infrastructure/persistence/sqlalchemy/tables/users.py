from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    String,
    Table,
    UniqueConstraint,
    true,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid_utils.compat import UUID

from backend.domain.core.entities.user import User
from backend.infrastructure.persistence.sqlalchemy.tables.base import (
    mapper_registry,
    metadata,
)

user_id_column: Column[UUID] = Column(
    "id",
    PG_UUID(as_uuid=True),
    primary_key=True,
    nullable=False,
)

user_email_column: Column[str] = Column(
    "email",
    String(255),
    nullable=False,
)

user_login_column: Column[str] = Column(
    "login",
    String(20),
    nullable=False,
)

user_username_column: Column[str] = Column(
    "username",
    String(20),
    nullable=False,
)

user_password_hash_column: Column[str] = Column(
    "password_hash",
    String(255),
    nullable=False,
)

user_is_active_column: Column[bool] = Column(
    "is_active",
    Boolean,
    nullable=False,
    server_default=true(),
)

users_table: Table = Table(
    "users",
    metadata,
    user_id_column,
    user_email_column,
    user_login_column,
    user_username_column,
    user_password_hash_column,
    user_is_active_column,
    CheckConstraint(
        "char_length(login) >= 3 AND char_length(login) <= 20",
        name="ck_users_login_len",
    ),
    CheckConstraint(
        r"login ~ '^[A-Za-z0-9]+$'",
        name="ck_users_login_alnum",
    ),
    CheckConstraint(
        r"email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'",
        name="ck_users_email_format",
    ),
    CheckConstraint(
        "char_length(username) >= 2 AND char_length(username) <= 20",
        name="ck_users_username_len",
    ),
    CheckConstraint(
        r"username !~ '\s'",
        name="ck_users_username_no_ws",
    ),
    CheckConstraint(
        r"char_length(password_hash) >= 20 AND password_hash ~ '^\$[a-z0-9-]+\$'",
        name="ck_users_password_hash_format",
    ),
    UniqueConstraint(user_email_column),
    UniqueConstraint(user_login_column),
    UniqueConstraint(user_username_column),
)

mapper_registry.map_imperatively(
    User,
    users_table,
    properties={"password": user_password_hash_column},
)
