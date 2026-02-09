"""Migrate roles.code to plain string storage.

Revision ID: 20260209_0002
Revises: 20260203_0001
Create Date: 2026-02-09 00:02:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision: str = "20260209_0002"
down_revision: str | None = "20260203_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_ROLES_TABLE: Final[str] = "roles"
_ROLE_CODE: Final[str] = "code"
_ROLE_CODE_LEN: Final[int] = 64
_LEGACY_ROLE_CODES: Final[tuple[str, ...]] = (
    "super_admin",
    "admin",
    "user",
)
_LEGACY_CHECK_NAME: Final[str] = "ck_roles_code_legacy"


def _bind() -> Connection:
    return op.get_bind()


def _check_constraints_for_role_code(bind: Connection) -> tuple[str, ...]:
    inspector = sa.inspect(bind)
    constraints = inspector.get_check_constraints(_ROLES_TABLE)
    names: list[str] = []
    for item in constraints:
        name = item.get("name")
        sql_text = str(item.get("sqltext") or "").lower()
        if not isinstance(name, str):
            continue
        if _ROLE_CODE not in sql_text:
            continue
        if any(code in sql_text for code in _LEGACY_ROLE_CODES):
            names.append(name)
    return tuple(names)


def _has_unique_constraint_on_role_code(bind: Connection) -> bool:
    inspector = sa.inspect(bind)
    constraints = inspector.get_unique_constraints(_ROLES_TABLE)
    for item in constraints:
        cols = tuple(item.get("column_names") or ())
        if cols == (_ROLE_CODE,):
            return True
    return False


def _has_check_constraint(bind: Connection, name: str) -> bool:
    inspector = sa.inspect(bind)
    constraints = inspector.get_check_constraints(_ROLES_TABLE)
    for item in constraints:
        constraint_name = item.get("name")
        if isinstance(constraint_name, str) and constraint_name == name:
            return True
    return False


def _assert_legacy_values_only(bind: Connection) -> None:
    stmt = sa.text(
        """
        SELECT code
        FROM roles
        GROUP BY code
        HAVING code NOT IN ('super_admin', 'admin', 'user')
        LIMIT 1
        """
    )
    row = bind.execute(stmt).first()
    if row is None:
        return
    role_code = row[0]
    raise RuntimeError(
        f"Cannot downgrade roles.code: non-legacy role exists: {role_code!r}"
    )


def upgrade() -> None:
    bind = _bind()
    for name in _check_constraints_for_role_code(bind):
        op.drop_constraint(op.f(name), _ROLES_TABLE, type_="check")

    op.alter_column(
        _ROLES_TABLE,
        _ROLE_CODE,
        existing_type=sa.String(),
        type_=sa.String(length=_ROLE_CODE_LEN),
        existing_nullable=False,
    )

    if not _has_unique_constraint_on_role_code(bind):
        op.create_unique_constraint(
            "uq_roles_code", _ROLES_TABLE, [_ROLE_CODE]
        )


def downgrade() -> None:
    bind = _bind()
    _assert_legacy_values_only(bind)

    op.alter_column(
        _ROLES_TABLE,
        _ROLE_CODE,
        existing_type=sa.String(length=_ROLE_CODE_LEN),
        type_=sa.String(length=11),
        existing_nullable=False,
    )

    if not _has_check_constraint(bind, _LEGACY_CHECK_NAME):
        op.create_check_constraint(
            op.f(_LEGACY_CHECK_NAME),
            _ROLES_TABLE,
            "code IN ('super_admin', 'admin', 'user')",
        )
