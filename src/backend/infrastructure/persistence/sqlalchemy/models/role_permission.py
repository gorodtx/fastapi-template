from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import mapper_registry, metadata

if TYPE_CHECKING:
    from sqlalchemy.orm import InstrumentedAttribute


role_permissions_table = Table(
    "role_permissions",
    metadata,
    Column(
        "role_id",
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column("code", String(64), primary_key=True, nullable=False),
)


user_roles_table = Table(
    "user_roles",
    metadata,
    Column(
        "user_id",
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "role_id",
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)


class RolePermissionModel:
    if TYPE_CHECKING:
        role_id: InstrumentedAttribute[uuid.UUID]
        code: InstrumentedAttribute[str]

    def __init__(self, *, role_id: uuid.UUID, code: str) -> None:
        self.role_id = role_id
        self.code = code

    def __repr__(self) -> str:
        return f"RolePermissionModel(role_id={self.role_id!r}, code={self.code!r})"


class UserRoleModel:
    if TYPE_CHECKING:
        user_id: InstrumentedAttribute[uuid.UUID]
        role_id: InstrumentedAttribute[uuid.UUID]

    def __init__(self, *, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        self.user_id = user_id
        self.role_id = role_id

    def __repr__(self) -> str:
        return f"UserRoleModel(user_id={self.user_id!r}, role_id={self.role_id!r})"


mapper_registry.map_imperatively(RolePermissionModel, role_permissions_table)
mapper_registry.map_imperatively(UserRoleModel, user_roles_table)
