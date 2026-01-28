from __future__ import annotations

from sqlalchemy import Boolean, Column, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid_utils.compat import UUID

from backend.domain.core.entities.user import User
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.domain.core.value_objects.password import Password
from backend.infrastructure.persistence.sqlalchemy.tables.base import (
    mapper_registry,
    metadata,
)
from backend.infrastructure.persistence.sqlalchemy.types import (
    EmailType,
    LoginType,
    PasswordHashType,
    UsernameType,
)

user_id_column: Column[UUID] = Column(
    "id",
    PG_UUID(as_uuid=True),
    primary_key=True,
    nullable=False,
)

user_email_column: Column[Email] = Column(
    "email",
    EmailType(),
    nullable=False,
)

user_login_column: Column[Login] = Column(
    "login",
    LoginType(),
    nullable=False,
)

user_username_column: Column[Username] = Column(
    "username",
    UsernameType(),
    nullable=False,
)

user_password_hash_column: Column[Password] = Column(
    "password_hash",
    PasswordHashType(),
    nullable=False,
)

user_is_active_column: Column[bool] = Column(
    "is_active",
    Boolean,
    nullable=False,
    default=True,
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
    UniqueConstraint(user_email_column),
    UniqueConstraint(user_login_column),
    UniqueConstraint(user_username_column),
)

_user_properties: dict[str, object] = {
    "_id": user_id_column,
    "_email": user_email_column,
    "_login": user_login_column,
    "_username": user_username_column,
    "_password": user_password_hash_column,
    "_is_active": user_is_active_column,
}

mapper_registry.map_imperatively(
    User,
    users_table,
    properties=_user_properties,
)
