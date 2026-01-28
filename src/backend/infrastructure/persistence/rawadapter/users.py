from __future__ import annotations

from collections.abc import Awaitable, Callable

import sqlalchemy as sa
from sqlalchemy import RowMapping
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import UUID

from backend.application.common.interfaces.ports.persistence.manager import (
    SessionProtocol,
)
from backend.infrastructure.persistence.records import UserRowRecord
from backend.infrastructure.persistence.sqlalchemy.tables.users import (
    users_table,
)
from backend.infrastructure.tools import convert_record


def _require_async_session(session: SessionProtocol) -> AsyncSession:
    if isinstance(session, AsyncSession):
        return session
    raise TypeError("SessionProtocol must be AsyncSession")


def q_get_user_row_by_id(
    user_id: UUID,
) -> Callable[[SessionProtocol], Awaitable[UserRowRecord | None]]:
    async def _q(session: SessionProtocol) -> UserRowRecord | None:
        async_session = _require_async_session(session)
        stmt = (
            sa.select(
                users_table.c.id,
                users_table.c.email.label("email"),
                users_table.c.login.label("login"),
                users_table.c.username.label("username"),
                users_table.c.password_hash.label("password_hash"),
                users_table.c.is_active,
            )
            .select_from(users_table)
            .where(users_table.c.id == user_id)
        )
        res = await async_session.execute(stmt)
        row: RowMapping | None = res.mappings().first()
        if row is None:
            return None
        return convert_record(dict(row), UserRowRecord)

    return _q


def q_get_user_row_by_email(
    email: str,
) -> Callable[[SessionProtocol], Awaitable[UserRowRecord | None]]:
    async def _q(session: SessionProtocol) -> UserRowRecord | None:
        async_session = _require_async_session(session)
        stmt = (
            sa.select(
                users_table.c.id,
                users_table.c.email.label("email"),
                users_table.c.login.label("login"),
                users_table.c.username.label("username"),
                users_table.c.password_hash.label("password_hash"),
                users_table.c.is_active,
            )
            .select_from(users_table)
            .where(users_table.c.email == email)
        )
        res = await async_session.execute(stmt)
        row: RowMapping | None = res.mappings().first()
        if row is None:
            return None
        return convert_record(dict(row), UserRowRecord)

    return _q


def q_upsert_user_row(
    row: UserRowRecord,
) -> Callable[[SessionProtocol], Awaitable[UserRowRecord]]:
    async def _q(session: SessionProtocol) -> UserRowRecord:
        async_session = _require_async_session(session)
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
            .returning(
                users_table.c.id,
                users_table.c.email.label("email"),
                users_table.c.login.label("login"),
                users_table.c.username.label("username"),
                users_table.c.password_hash.label("password_hash"),
                users_table.c.is_active,
            )
        )
        res = await async_session.execute(stmt)
        row_mapping: RowMapping | None = res.mappings().first()
        if row_mapping is None:
            raise RuntimeError("Failed to upsert user row")
        return convert_record(dict(row_mapping), UserRowRecord)

    return _q


def q_delete_user(
    user_id: UUID,
) -> Callable[[SessionProtocol], Awaitable[bool]]:
    async def _q(session: SessionProtocol) -> bool:
        async_session = _require_async_session(session)
        stmt = (
            sa.delete(users_table)
            .where(users_table.c.id == user_id)
            .returning(users_table.c.id)
        )
        res = await async_session.execute(stmt)
        deleted = res.scalar_one_or_none()
        return deleted is not None

    return _q
