from __future__ import annotations

from sqlalchemy.dialects import postgresql
from uuid_utils.compat import UUID

from backend.infrastructure.persistence.rawadapter.users import (
    _lock_user_row_by_id_stmt,
)


def test_lock_user_stmt_uses_for_update_nowait() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    stmt = _lock_user_row_by_id_stmt(user_id)
    sql = str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "FOR UPDATE NOWAIT" in sql
