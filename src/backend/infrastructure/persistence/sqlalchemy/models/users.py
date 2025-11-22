from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import mapper_registry, metadata

users_table = Table(
    "users",
    metadata,
    Column("id", PG_UUID(as_uuid=True), primary_key=True, nullable=False),
    Column("email", String(255), nullable=False),
    Column("login", String(20), nullable=False),
    Column("username", String(20), nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("is_active", Boolean, nullable=False),
    UniqueConstraint("email"),
    UniqueConstraint("login"),
    UniqueConstraint("username"),
)


class UserModel:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        email: str,
        login: str,
        username: str,
        password_hash: str,
        is_active: bool,
    ) -> None:
        self.id = id
        self.email = email
        self.login = login
        self.username = username
        self.password_hash = password_hash
        self.is_active = is_active

    def __repr__(self) -> str:
        return (
            f"UserModel(id={self.id!r}, email={self.email!r}, "
            f"login={self.login!r}, username={self.username!r}, "
            f"is_active={self.is_active!r})"
        )


mapper_registry.map_imperatively(UserModel, users_table)
