"""Enforce lowercase email storage.

We canonicalize emails to lowercase to ensure case-insensitive uniqueness and
stable lookup semantics.

Migration steps:
1) Detect collisions that would be introduced by lowercasing (fail fast).
2) Backfill existing rows: email = lower(email).
3) Enforce invariant at DB level: email = lower(email).

Revision ID: 20260309_0007
Revises: 20260309_0006
Create Date: 2026-03-09 00:07:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision: str = "20260309_0007"
down_revision: str | None = "20260309_0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TABLE: str = "users"
_CK_EMAIL_LOWER: str = "ck_users_email_lowercase"


def _bind() -> Connection:
    return op.get_bind()


def upgrade() -> None:
    bind = _bind()

    collision_stmt = sa.text(
        """
        SELECT lower(email) AS canonical, count(*) AS cnt
        FROM users
        GROUP BY lower(email)
        HAVING count(*) > 1
        LIMIT 1
        """
    )
    collision_row = bind.execute(collision_stmt).first()
    if collision_row is not None:
        canonical = collision_row[0]
        raise RuntimeError(
            "Cannot enforce lowercase emails: collision detected for "
            f"{canonical!r}"
        )

    bind.execute(
        sa.text(
            "UPDATE users SET email = lower(email) WHERE email <> lower(email)"
        )
    )
    op.create_check_constraint(_CK_EMAIL_LOWER, _TABLE, "email = lower(email)")


def downgrade() -> None:
    op.drop_constraint(_CK_EMAIL_LOWER, _TABLE, type_="check")
