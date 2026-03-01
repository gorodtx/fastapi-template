"""Enable pg_stat_statements extension for DB observability.

Revision ID: 20260301_0005
Revises: 20260210_0004
Create Date: 2026-03-01 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260301_0005"
down_revision: str | None = "20260210_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS pg_stat_statements")
