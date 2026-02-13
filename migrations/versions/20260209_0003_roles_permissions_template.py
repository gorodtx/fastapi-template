"""Template migration for adding roles and permission bindings.

Fill `NEW_ROLES` and optionally `ROLE_DESCRIPTIONS` / `ROLE_USER_BINDINGS`,
then run `uv run alembic upgrade head`.

Revision ID: 20260209_0003
Revises: 20260209_0002
Create Date: 2026-02-09 00:03:00.000000
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterable, Sequence
from typing import Final

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection
from sqlalchemy.sql import Select

# revision identifiers, used by Alembic.
revision: str = "20260209_0003"
down_revision: str | None = "20260209_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_ROLE_CODE_PATTERN: Final[str] = r"^[a-z][a-z0-9_]{2,63}$"
_PERMISSION_CODE_PATTERN: Final[str] = (
    r"^[a-z][a-z0-9_]*:[a-z][a-z0-9_]{1,63}$"
)

# Fill this mapping with new roles and their permissions.
NEW_ROLES: Final[dict[str, frozenset[str]]] = {}

# Optional: extra permissions for super_admin. If provided, they will be
# merged into NEW_ROLES["super_admin"].
SUPER_ADMIN_EXTRA_PERMISSIONS: Final[frozenset[str]] = frozenset()

# Optional role descriptions.
ROLE_DESCRIPTIONS: Final[dict[str, str | None]] = {}

# Optional assignments by user login.
ROLE_USER_BINDINGS: Final[dict[str, tuple[str, ...]]] = {}

_ROLES_TABLE = sa.table(
    "roles",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("code", sa.String(length=64)),
    sa.column("description", sa.String(length=255)),
)
_PERMISSIONS_TABLE = sa.table(
    "permissions",
    sa.column("code", sa.String(length=64)),
    sa.column("description", sa.String(length=255)),
)
_ROLE_PERMISSIONS_TABLE = sa.table(
    "role_permissions",
    sa.column("role_id", postgresql.UUID(as_uuid=True)),
    sa.column("permission_code", sa.String(length=64)),
)
_USER_ROLES_TABLE = sa.table(
    "user_roles",
    sa.column("user_id", postgresql.UUID(as_uuid=True)),
    sa.column("role_id", postgresql.UUID(as_uuid=True)),
)
_USERS_TABLE = sa.table(
    "users",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("login", sa.String(length=20)),
)


def _roles_payload() -> dict[str, frozenset[str]]:
    if not SUPER_ADMIN_EXTRA_PERMISSIONS:
        return NEW_ROLES
    merged = set(NEW_ROLES.get("super_admin", frozenset()))
    merged.update(SUPER_ADMIN_EXTRA_PERMISSIONS)
    return {**NEW_ROLES, "super_admin": frozenset(merged)}


def _bind() -> Connection:
    return op.get_bind()


def _validate_payload() -> None:
    roles_payload = _roles_payload()
    role_pattern = re.compile(_ROLE_CODE_PATTERN)
    permission_pattern = re.compile(_PERMISSION_CODE_PATTERN)
    unknown_descriptions = set(ROLE_DESCRIPTIONS) - set(roles_payload)
    if unknown_descriptions:
        raise RuntimeError(
            "ROLE_DESCRIPTIONS contains unknown role codes: "
            f"{sorted(unknown_descriptions)!r}"
        )
    for role_code, permissions in roles_payload.items():
        if not isinstance(role_code, str):
            raise RuntimeError("Role code must be str")
        if role_pattern.fullmatch(role_code) is None:
            raise RuntimeError(f"Invalid role code format: {role_code!r}")
        if not permissions:
            raise RuntimeError(
                f"Role {role_code!r} must have at least one permission"
            )
        for permission_code in permissions:
            if not isinstance(permission_code, str):
                raise RuntimeError(
                    f"Permission code must be str: {permission_code!r}"
                )
            if permission_pattern.fullmatch(permission_code) is None:
                raise RuntimeError(
                    f"Invalid permission code format: {permission_code!r}"
                )
    for role_code in ROLE_USER_BINDINGS:
        if role_code not in roles_payload:
            raise RuntimeError(
                f"ROLE_USER_BINDINGS contains unknown role code: {role_code!r}"
            )
        logins = ROLE_USER_BINDINGS[role_code]
        if len(logins) != len(set(logins)):
            raise RuntimeError(
                f"ROLE_USER_BINDINGS contains duplicate logins for {role_code!r}"
            )


def _role_id(role_code: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_OID, f"role:{role_code}")


def _upsert_role(
    bind: Connection, role_code: str, description: str | None
) -> uuid.UUID:
    role_id = _role_id(role_code)
    stmt = (
        pg_insert(_ROLES_TABLE)
        .values(id=role_id, code=role_code, description=description)
        .on_conflict_do_update(
            index_elements=[_ROLES_TABLE.c.code],
            set_={"description": description},
        )
    )
    bind.execute(stmt)
    select_stmt: Select[tuple[uuid.UUID]] = sa.select(_ROLES_TABLE.c.id).where(
        _ROLES_TABLE.c.code == role_code
    )
    selected = bind.execute(select_stmt).scalar_one()
    return selected


def _upsert_permissions(
    bind: Connection, permission_codes: Iterable[str]
) -> None:
    for code in permission_codes:
        stmt = (
            pg_insert(_PERMISSIONS_TABLE)
            .values(code=code, description=None)
            .on_conflict_do_nothing(index_elements=[_PERMISSIONS_TABLE.c.code])
        )
        bind.execute(stmt)


def _sync_role_permissions(
    bind: Connection, role_id: uuid.UUID, target_codes: frozenset[str]
) -> None:
    select_stmt = sa.select(_ROLE_PERMISSIONS_TABLE.c.permission_code).where(
        _ROLE_PERMISSIONS_TABLE.c.role_id == role_id
    )
    current_codes = {
        row[0]
        for row in bind.execute(select_stmt).all()
        if isinstance(row[0], str)
    }

    missing = sorted(target_codes - current_codes)
    for code in missing:
        stmt = (
            pg_insert(_ROLE_PERMISSIONS_TABLE)
            .values(role_id=role_id, permission_code=code)
            .on_conflict_do_nothing(
                index_elements=[
                    _ROLE_PERMISSIONS_TABLE.c.role_id,
                    _ROLE_PERMISSIONS_TABLE.c.permission_code,
                ]
            )
        )
        bind.execute(stmt)

    extra = sorted(current_codes - target_codes)
    if extra:
        delete_stmt = sa.delete(_ROLE_PERMISSIONS_TABLE).where(
            _ROLE_PERMISSIONS_TABLE.c.role_id == role_id,
            _ROLE_PERMISSIONS_TABLE.c.permission_code.in_(extra),
        )
        bind.execute(delete_stmt)


def _bind_users_to_role(
    bind: Connection, role_id: uuid.UUID, user_logins: tuple[str, ...]
) -> None:
    for login in user_logins:
        user_id_stmt = sa.select(_USERS_TABLE.c.id).where(
            _USERS_TABLE.c.login == login
        )
        user_id = bind.execute(user_id_stmt).scalar_one_or_none()
        if user_id is None:
            raise RuntimeError(
                f"Cannot bind role: user with login {login!r} not found"
            )
        bind_stmt = (
            pg_insert(_USER_ROLES_TABLE)
            .values(user_id=user_id, role_id=role_id)
            .on_conflict_do_nothing(
                index_elements=[
                    _USER_ROLES_TABLE.c.user_id,
                    _USER_ROLES_TABLE.c.role_id,
                ]
            )
        )
        bind.execute(bind_stmt)


def upgrade() -> None:
    _validate_payload()
    roles_payload = _roles_payload()
    if not roles_payload:
        return
    bind = _bind()
    for role_code, permission_codes in roles_payload.items():
        description = ROLE_DESCRIPTIONS.get(role_code)
        role_id = _upsert_role(bind, role_code, description)
        _upsert_permissions(bind, permission_codes)
        _sync_role_permissions(bind, role_id, permission_codes)
        bindings = ROLE_USER_BINDINGS.get(role_code, ())
        _bind_users_to_role(bind, role_id, bindings)


def downgrade() -> None:
    roles_payload = _roles_payload()
    if not roles_payload:
        return
    bind = _bind()
    for role_code in roles_payload:
        role_id_stmt = sa.select(_ROLES_TABLE.c.id).where(
            _ROLES_TABLE.c.code == role_code
        )
        role_id = bind.execute(role_id_stmt).scalar_one_or_none()
        if role_id is None:
            continue
        bind.execute(
            sa.delete(_USER_ROLES_TABLE).where(
                _USER_ROLES_TABLE.c.role_id == role_id
            )
        )
        bind.execute(
            sa.delete(_ROLE_PERMISSIONS_TABLE).where(
                _ROLE_PERMISSIONS_TABLE.c.role_id == role_id
            )
        )
        bind.execute(
            sa.delete(_ROLES_TABLE).where(_ROLES_TABLE.c.id == role_id)
        )
