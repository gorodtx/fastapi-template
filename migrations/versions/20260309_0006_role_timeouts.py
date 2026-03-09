"""Set Postgres safety timeouts for the application role.

These defaults act as a safety-net against:
- runaway queries (statement_timeout),
- indefinite lock waits (lock_timeout),
- long-lived idle transactions (idle_in_transaction_session_timeout).

In this template, the app and migrations often run as the same DB user in dev;
we therefore keep the defaults conservative.

Revision ID: 20260309_0006
Revises: 20260301_0005
Create Date: 2026-03-09 00:06:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260309_0006"
down_revision: str | None = "20260301_0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_STATEMENT_TIMEOUT: str = "30s"
_LOCK_TIMEOUT: str = "1s"
_IDLE_IN_TX_TIMEOUT: str = "30s"


def upgrade() -> None:
    op.execute(
        f"ALTER ROLE CURRENT_USER SET statement_timeout = '{_STATEMENT_TIMEOUT}'"
    )
    op.execute(f"ALTER ROLE CURRENT_USER SET lock_timeout = '{_LOCK_TIMEOUT}'")
    op.execute(
        "ALTER ROLE CURRENT_USER SET idle_in_transaction_session_timeout = "
        f"'{_IDLE_IN_TX_TIMEOUT}'"
    )


def downgrade() -> None:
    op.execute("ALTER ROLE CURRENT_USER RESET statement_timeout")
    op.execute("ALTER ROLE CURRENT_USER RESET lock_timeout")
    op.execute(
        "ALTER ROLE CURRENT_USER RESET idle_in_transaction_session_timeout"
    )
