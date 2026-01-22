from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import UUID

from backend.domain.core.constants.rbac import SystemRole
from backend.infrastructure.persistence.records import UserRoleCodeRecord
from backend.infrastructure.persistence.sqlalchemy.tables.role import roles_table
from backend.infrastructure.persistence.sqlalchemy.tables.role_permission import (
    user_roles_table,
)


def q_get_user_role_codes(
    user_id: UUID,
) -> Callable[[AsyncSession], Awaitable[list[UserRoleCodeRecord]]]:
    async def _q(session: AsyncSession) -> list[UserRoleCodeRecord]:
        join_stmt = user_roles_table.join(
            roles_table, user_roles_table.c.role_id == roles_table.c.id
        )
        stmt = (
            sa.select(
                user_roles_table.c.user_id.label("user_id"),
                sa.cast(roles_table.c.code, sa.String).label("role"),
            )
            .select_from(join_stmt)
            .where(user_roles_table.c.user_id == user_id)
        )
        res = await session.execute(stmt)
        rows = res.mappings().all()
        return [UserRoleCodeRecord(user_id=row["user_id"], role=row["role"]) for row in rows]

    return _q


def q_get_role_ids_by_codes(
    codes: Sequence[SystemRole],
) -> Callable[[AsyncSession], Awaitable[list[tuple[SystemRole, UUID]]]]:
    async def _q(session: AsyncSession) -> list[tuple[SystemRole, UUID]]:
        if not codes:
            return []
        stmt = sa.select(roles_table.c.code, roles_table.c.id).where(roles_table.c.code.in_(codes))
        res = await session.execute(stmt)
        out: list[tuple[SystemRole, UUID]] = []
        for role_code, role_id in res.all():
            out.append((role_code, role_id))
        return out

    return _q


def q_replace_user_roles(
    user_id: UUID, role_ids: list[UUID]
) -> Callable[[AsyncSession], Awaitable[None]]:
    async def _q(session: AsyncSession) -> None:
        await session.execute(
            sa.delete(user_roles_table).where(user_roles_table.c.user_id == user_id)
        )
        if role_ids:
            payload = [{"user_id": user_id, "role_id": rid} for rid in role_ids]
            await session.execute(sa.insert(user_roles_table), payload)

    return _q


def q_list_user_ids_by_role_id(
    role_id: UUID,
) -> Callable[[AsyncSession], Awaitable[list[UUID]]]:
    async def _q(session: AsyncSession) -> list[UUID]:
        stmt = sa.select(user_roles_table.c.user_id).where(user_roles_table.c.role_id == role_id)
        res = await session.execute(stmt)
        return [row[0] for row in res.all()]

    return _q
