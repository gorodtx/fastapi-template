"""Create users + RBAC tables and seed system roles/permissions.

Revision ID: 20260203_0001
Revises:
Create Date: 2026-02-03 00:00:00.000000
"""

import json
import os
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, TypeGuard

import sqlalchemy as sa
from alembic import op
from argon2 import PasswordHasher, Type
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.domain.core.constants.permission_codes import ALL_PERMISSION_CODES
from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.constants.rbac_registry import ROLE_PERMISSIONS

# revision identifiers, used by Alembic.
revision: str = "20260203_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_BOOTSTRAP_ENV_VAR: Final[str] = "RBAC_BOOTSTRAP_USERS"
_ARGON2_TIME_COST: Final[int] = 3
_ARGON2_MEMORY_COST: Final[int] = 65536
_ARGON2_PARALLELISM: Final[int] = 4
_ARGON2_HASH_LEN: Final[int] = 32
_ARGON2_SALT_LEN: Final[int] = 16


@dataclass(frozen=True, slots=True)
class _BootstrapUser:
    email: str
    login: str
    username: str
    password_hash: str
    roles: tuple[SystemRole, ...]


def _role_id(role: SystemRole) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_OID, f"role:{role.value}")


def _load_bootstrap_users() -> list[_BootstrapUser]:
    raw = os.getenv(_BOOTSTRAP_ENV_VAR, "").strip()
    if not raw:
        return []

    try:
        data: object = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{_BOOTSTRAP_ENV_VAR} must be valid JSON") from exc

    items = _ensure_list(data, f"{_BOOTSTRAP_ENV_VAR} must be a JSON list")
    users: list[_BootstrapUser] = []
    for item in items:
        payload = _normalize_payload(item)
        users.append(_parse_bootstrap_user(payload))
    return users


def _parse_bootstrap_user(payload: Mapping[str, object]) -> _BootstrapUser:
    email = _require_str(payload, "email")
    login = _require_str(payload, "login")
    username = _require_str(payload, "username")
    raw_password = _require_str(payload, "password")
    password_hash = _hash_password(raw_password)
    roles = _parse_roles(payload.get("roles"))
    return _BootstrapUser(
        email=email,
        login=login,
        username=username,
        password_hash=password_hash,
        roles=roles,
    )


def _require_str(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{_BOOTSTRAP_ENV_VAR} field '{key}' must be a non-empty string"
        )
    return value.strip()


def _normalize_payload(raw: object) -> dict[str, object]:
    if not _is_str_object_dict(raw):
        raise ValueError(f"{_BOOTSTRAP_ENV_VAR} entries must be JSON objects")
    payload: dict[str, object] = {}
    for key, value in raw.items():
        payload[key] = value
    return payload


def _hash_password(raw_password: str) -> str:
    hasher = PasswordHasher(
        time_cost=_ARGON2_TIME_COST,
        memory_cost=_ARGON2_MEMORY_COST,
        parallelism=_ARGON2_PARALLELISM,
        hash_len=_ARGON2_HASH_LEN,
        salt_len=_ARGON2_SALT_LEN,
        type=Type.ID,
    )
    return hasher.hash(raw_password)


def _parse_roles(raw: object) -> tuple[SystemRole, ...]:
    if raw is None:
        return (SystemRole.SUPER_ADMIN,)
    role_items = _ensure_list(
        raw, f"{_BOOTSTRAP_ENV_VAR} field 'roles' must be a list of strings"
    )
    roles: set[SystemRole] = set()
    for item in role_items:
        if not isinstance(item, str):
            raise ValueError(
                f"{_BOOTSTRAP_ENV_VAR} role values must be strings"
            )
        try:
            roles.add(SystemRole(item))
        except ValueError as exc:
            raise ValueError(
                f"Unknown role {item!r} in {_BOOTSTRAP_ENV_VAR}"
            ) from exc
    if not roles:
        raise ValueError(f"{_BOOTSTRAP_ENV_VAR} field 'roles' cannot be empty")
    return tuple(sorted(roles, key=lambda role: role.value))


def _ensure_list(value: object, error: str) -> list[object]:
    if not _is_object_list(value):
        raise ValueError(error)
    return list(value)


def _is_str_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def upgrade() -> None:
    users_table = op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("login", sa.String(20), nullable=False),
        sa.Column("username", sa.String(20), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("login"),
        sa.UniqueConstraint("username"),
    )

    roles_table = op.create_table(
        "roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.Enum(
                SystemRole,
                native_enum=False,
                values_callable=lambda enum_cls: [e.value for e in enum_cls],
            ),
            nullable=False,
        ),
        sa.Column("description", sa.String(255), nullable=True),
        sa.UniqueConstraint("code"),
    )

    permissions_table = op.create_table(
        "permissions",
        sa.Column("code", sa.String(64), primary_key=True, nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
    )

    role_permissions_table = op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "roles.id",
                name="fk_role_permissions_role_id__roles_id",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "permission_code",
            sa.String(64),
            sa.ForeignKey(
                "permissions.code",
                name="fk_role_permissions_permission_code__permissions_code",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),
    )

    user_roles_table = op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                name="fk_user_roles_user_id__users_id",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "roles.id",
                name="fk_user_roles_role_id__roles_id",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),
    )

    op.create_index(
        "ix_role_permissions_role_id", "role_permissions", ["role_id"]
    )
    op.create_index(
        "ix_role_permissions_permission_code",
        "role_permissions",
        ["permission_code"],
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    role_rows = [
        {
            "id": _role_id(role),
            "code": role.value,
            "description": None,
        }
        for role in SystemRole
    ]
    op.bulk_insert(roles_table, role_rows)

    permission_rows = [
        {
            "code": permission.value,
            "description": None,
        }
        for permission in sorted(
            ALL_PERMISSION_CODES, key=lambda item: item.value
        )
    ]
    op.bulk_insert(permissions_table, permission_rows)

    role_permission_rows: list[dict[str, object]] = []
    for role, permissions in ROLE_PERMISSIONS.items():
        role_id = _role_id(role)
        for permission in sorted(permissions, key=lambda item: item.value):
            role_permission_rows.append(
                {
                    "role_id": role_id,
                    "permission_code": permission.value,
                }
            )
    if role_permission_rows:
        op.bulk_insert(role_permissions_table, role_permission_rows)

    bootstrap_users = _load_bootstrap_users()
    if not bootstrap_users:
        return

    connection = op.get_bind()
    for user in bootstrap_users:
        user_id = _find_user_id(connection, users_table, user.login)
        if user_id is None:
            user_id = uuid.uuid4()
            connection.execute(
                users_table.insert().values(
                    id=user_id,
                    email=user.email,
                    login=user.login,
                    username=user.username,
                    password_hash=user.password_hash,
                    is_active=True,
                )
            )

        user_role_rows = [
            {"user_id": user_id, "role_id": _role_id(role)}
            for role in user.roles
        ]
        if user_role_rows:
            stmt = pg_insert(user_roles_table).values(user_role_rows)
            stmt = stmt.on_conflict_do_nothing()
            connection.execute(stmt)


def _find_user_id(
    connection: sa.Connection,
    users_table: sa.Table,
    login: str,
) -> uuid.UUID | None:
    result = connection.execute(
        sa.select(users_table.c.id).where(users_table.c.login == login)
    ).first()
    if result is None:
        return None
    candidate = result[0]
    if not isinstance(candidate, uuid.UUID):
        raise ValueError("Unexpected user id type during bootstrap")
    return candidate


def downgrade() -> None:
    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_index(
        "ix_role_permissions_permission_code", table_name="role_permissions"
    )
    op.drop_index("ix_role_permissions_role_id", table_name="role_permissions")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
