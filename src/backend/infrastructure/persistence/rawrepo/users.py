from __future__ import annotations

from collections.abc import Awaitable, Callable

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import UUID

from backend.infrastructure.persistence.records import UserRowRecord
from backend.infrastructure.persistence.sqlalchemy.tables.users import users_table


def q_get_user_row_by_id(
    user_id: UUID,
) -> Callable[[AsyncSession], Awaitable[UserRowRecord | None]]:
    async def _q(session: AsyncSession) -> UserRowRecord | None:
        stmt = (
            sa.select(
                users_table.c.id,
                sa.cast(users_table.c.email, sa.String).label("email"),
                sa.cast(users_table.c.login, sa.String).label("login"),
                sa.cast(users_table.c.username, sa.String).label("username"),
                sa.cast(users_table.c.password_hash, sa.String).label("password_hash"),
                users_table.c.is_active,
            )
            .select_from(users_table)
            .where(users_table.c.id == user_id)
        )
        res = await session.execute(stmt)
        row = res.mappings().first()
        if row is None:
            return None
        return UserRowRecord(
            id=row["id"],
            email=row["email"],
            login=row["login"],
            username=row["username"],
            password_hash=row["password_hash"],
            is_active=row["is_active"],
        )

    return _q


def q_upsert_user_row(
    row: UserRowRecord,
) -> Callable[[AsyncSession], Awaitable[UserRowRecord]]:
    async def _q(session: AsyncSession) -> UserRowRecord:
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
                sa.cast(users_table.c.email, sa.String).label("email"),
                sa.cast(users_table.c.login, sa.String).label("login"),
                sa.cast(users_table.c.username, sa.String).label("username"),
                sa.cast(users_table.c.password_hash, sa.String).label("password_hash"),
                users_table.c.is_active,
            )
        )
        res = await session.execute(stmt)
        row_mapping = res.mappings().first()
        if row_mapping is None:
            raise RuntimeError("Failed to upsert user row")
        return UserRowRecord(
            id=row_mapping["id"],
            email=row_mapping["email"],
            login=row_mapping["login"],
            username=row_mapping["username"],
            password_hash=row_mapping["password_hash"],
            is_active=row_mapping["is_active"],
        )

    return _q


def q_delete_user(user_id: UUID) -> Callable[[AsyncSession], Awaitable[bool]]:
    async def _q(session: AsyncSession) -> bool:
        stmt = sa.delete(users_table).where(users_table.c.id == user_id).returning(users_table.c.id)
        res = await session.execute(stmt)
        deleted = res.scalar_one_or_none()
        return deleted is not None

    return _q
