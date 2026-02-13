from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence

import sqlalchemy as sa
from sqlalchemy import RowMapping
from uuid_utils.compat import UUID

from backend.application.common.interfaces.ports.persistence.manager import (
    SessionProtocol,
)
from backend.domain.core.types.rbac import RoleCode
from backend.infrastructure.persistence.mappers.rbac import value_to_uuid
from backend.infrastructure.persistence.records import UserRoleCodeRecord
from backend.infrastructure.persistence.sqlalchemy.session_db import (
    require_async_session,
)
from backend.infrastructure.persistence.sqlalchemy.tables.role import (
    roles_table,
)
from backend.infrastructure.persistence.sqlalchemy.tables.role_permission import (
    role_permissions_table,
    user_roles_table,
)
from backend.infrastructure.tools.msgspec_convert import convert_record


def q_get_user_role_codes(
    user_id: UUID,
) -> Callable[[SessionProtocol], Awaitable[list[UserRoleCodeRecord]]]:
    async def _q(session: SessionProtocol) -> list[UserRoleCodeRecord]:
        async_session = require_async_session(session)
        join_stmt = user_roles_table.join(
            roles_table, user_roles_table.c.role_id == roles_table.c.id
        )
        stmt = (
            sa.select(
                user_roles_table.c.user_id.label("user_id"),
                roles_table.c.code.label("role"),
            )
            .select_from(join_stmt)
            .where(user_roles_table.c.user_id == user_id)
        )
        res = await async_session.execute(stmt)
        rows: Sequence[RowMapping] = res.mappings().all()
        return [convert_record(dict(row), UserRoleCodeRecord) for row in rows]

    return _q


def q_get_role_ids_by_codes(
    codes: Sequence[RoleCode],
) -> Callable[[SessionProtocol], Awaitable[list[tuple[RoleCode, UUID]]]]:
    async def _q(session: SessionProtocol) -> list[tuple[RoleCode, UUID]]:
        async_session = require_async_session(session)
        if not codes:
            return []
        code_values = list(codes)
        stmt = sa.select(roles_table.c.code, roles_table.c.id).where(
            roles_table.c.code.in_(code_values)
        )
        res = await async_session.execute(stmt)
        out: list[tuple[RoleCode, UUID]] = []
        for role_code, role_id in res.all():
            out.append((str(role_code), value_to_uuid(role_id)))
        return out

    return _q


def q_replace_user_roles(
    user_id: UUID, role_ids: list[UUID]
) -> Callable[[SessionProtocol], Awaitable[None]]:
    async def _q(session: SessionProtocol) -> None:
        async_session = require_async_session(session)
        await async_session.execute(
            sa.delete(user_roles_table).where(
                user_roles_table.c.user_id == user_id
            )
        )
        if role_ids:
            payload = [
                {"user_id": user_id, "role_id": rid} for rid in role_ids
            ]
            await async_session.execute(sa.insert(user_roles_table), payload)

    return _q


def q_list_user_ids_by_role_id(
    role_id: UUID,
) -> Callable[[SessionProtocol], Awaitable[list[UUID]]]:
    async def _q(session: SessionProtocol) -> list[UUID]:
        async_session = require_async_session(session)
        stmt = sa.select(user_roles_table.c.user_id).where(
            user_roles_table.c.role_id == role_id
        )
        res = await async_session.execute(stmt)
        return [value_to_uuid(row[0]) for row in res.all()]

    return _q


def q_get_user_permission_codes(
    user_id: UUID,
) -> Callable[[SessionProtocol], Awaitable[list[str]]]:
    async def _q(session: SessionProtocol) -> list[str]:
        async_session = require_async_session(session)
        join_stmt = user_roles_table.join(
            roles_table, user_roles_table.c.role_id == roles_table.c.id
        ).join(
            role_permissions_table,
            role_permissions_table.c.role_id == roles_table.c.id,
        )
        stmt = (
            sa.select(sa.distinct(role_permissions_table.c.permission_code))
            .select_from(join_stmt)
            .where(user_roles_table.c.user_id == user_id)
        )
        res = await async_session.execute(stmt)
        return [str(row[0]) for row in res.all() if isinstance(row[0], str)]

    return _q
