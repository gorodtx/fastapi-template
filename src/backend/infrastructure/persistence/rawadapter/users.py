from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence

import sqlalchemy as sa
from sqlalchemy import RowMapping
from sqlalchemy.dialects.postgresql import insert as pg_insert
from uuid_utils.compat import UUID

from backend.application.common.interfaces.ports.persistence.manager import (
    SessionProtocol,
)
from backend.infrastructure.persistence.mappers.rows import (
    map_many,
    map_one,
)
from backend.infrastructure.persistence.rawadapter.sql_helpers import (
    USER_ROW_COLUMNS,
    select_user_rows,
)
from backend.infrastructure.persistence.records import UserRowRecord
from backend.infrastructure.persistence.sqlalchemy.session_db import (
    require_async_session,
)
from backend.infrastructure.persistence.sqlalchemy.tables.users import (
    users_table,
)


def _lock_user_row_by_id_stmt(user_id: UUID) -> sa.Select[tuple]:
    return select_user_rows(users_table.c.id == user_id).with_for_update(
        nowait=True
    )


def q_get_user_row_by_id(
    user_id: UUID,
) -> Callable[[SessionProtocol], Awaitable[UserRowRecord | None]]:
    async def _q(session: SessionProtocol) -> UserRowRecord | None:
        async_session = require_async_session(session)
        stmt = select_user_rows(users_table.c.id == user_id)
        res = await async_session.execute(stmt)
        row: RowMapping | None = res.mappings().first()
        return map_one(row, UserRowRecord)

    return _q


def q_lock_user_row_by_id_nowait(
    user_id: UUID,
) -> Callable[[SessionProtocol], Awaitable[UserRowRecord | None]]:
    async def _q(session: SessionProtocol) -> UserRowRecord | None:
        async_session = require_async_session(session)
        stmt = _lock_user_row_by_id_stmt(user_id)
        res = await async_session.execute(stmt)
        row: RowMapping | None = res.mappings().first()
        return map_one(row, UserRowRecord)

    return _q


def q_get_user_row_by_email(
    email: str,
) -> Callable[[SessionProtocol], Awaitable[UserRowRecord | None]]:
    async def _q(session: SessionProtocol) -> UserRowRecord | None:
        async_session = require_async_session(session)
        stmt = select_user_rows(users_table.c.email == email)
        res = await async_session.execute(stmt)
        row: RowMapping | None = res.mappings().first()
        return map_one(row, UserRowRecord)

    return _q


def q_get_user_rows_by_ids(
    user_ids: Sequence[UUID],
) -> Callable[[SessionProtocol], Awaitable[list[UserRowRecord]]]:
    async def _q(session: SessionProtocol) -> list[UserRowRecord]:
        async_session = require_async_session(session)
        id_values = list(user_ids)
        if not id_values:
            return []
        stmt = select_user_rows(users_table.c.id.in_(id_values))
        res = await async_session.execute(stmt)
        rows: Sequence[RowMapping] = res.mappings().all()
        return map_many(rows, UserRowRecord)

    return _q


def q_upsert_user_row(
    row: UserRowRecord,
) -> Callable[[SessionProtocol], Awaitable[UserRowRecord]]:
    async def _q(session: SessionProtocol) -> UserRowRecord:
        async_session = require_async_session(session)
        values = {
            "id": row.id,
            "email": row.email,
            "login": row.login,
            "username": row.username,
            "password_hash": row.password_hash,
            "is_active": row.is_active,
        }
        stmt = (
            pg_insert(users_table)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[users_table.c.id],
                set_=values,
            )
            .returning(*USER_ROW_COLUMNS)
        )
        res = await async_session.execute(stmt)
        row_mapping: RowMapping | None = res.mappings().first()
        converted = map_one(row_mapping, UserRowRecord)
        if converted is None:
            raise RuntimeError("Failed to upsert user row")
        return converted

    return _q


def q_delete_user(
    user_id: UUID,
) -> Callable[[SessionProtocol], Awaitable[bool]]:
    async def _q(session: SessionProtocol) -> bool:
        async_session = require_async_session(session)
        stmt = (
            sa.delete(users_table)
            .where(users_table.c.id == user_id)
            .returning(users_table.c.id)
        )
        res = await async_session.execute(stmt)
        deleted = res.scalar_one_or_none()
        return deleted is not None

    return _q
