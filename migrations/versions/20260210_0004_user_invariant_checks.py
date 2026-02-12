"""Add DB checks for user identity invariants.

Revision ID: 20260210_0004
Revises: 20260209_0003
Create Date: 2026-02-10 00:04:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260210_0004"
down_revision: str | None = "20260209_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_users_login_len",
        "users",
        "char_length(login) >= 3 AND char_length(login) <= 20",
    )
    op.create_check_constraint(
        "ck_users_login_alnum",
        "users",
        r"login ~ '^[A-Za-z0-9]+$'",
    )
    op.create_check_constraint(
        "ck_users_email_format",
        "users",
        r"email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'",
    )
    op.create_check_constraint(
        "ck_users_username_len",
        "users",
        "char_length(username) >= 2 AND char_length(username) <= 20",
    )
    op.create_check_constraint(
        "ck_users_username_no_ws",
        "users",
        r"username !~ '\s'",
    )
    op.create_check_constraint(
        "ck_users_password_hash_format",
        "users",
        r"char_length(password_hash) >= 20 AND password_hash ~ '^\$[a-z0-9-]+\$'",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_password_hash_format", "users", type_="check")
    op.drop_constraint("ck_users_username_no_ws", "users", type_="check")
    op.drop_constraint("ck_users_username_len", "users", type_="check")
    op.drop_constraint("ck_users_email_format", "users", type_="check")
    op.drop_constraint("ck_users_login_alnum", "users", type_="check")
    op.drop_constraint("ck_users_login_len", "users", type_="check")
