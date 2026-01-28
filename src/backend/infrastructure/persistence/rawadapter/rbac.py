from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import UUID

from backend.application.common.interfaces.ports.persistence.manager import (
    SessionProtocol,
)
from backend.domain.core.constants.rbac import SystemRole
from backend.infrastructure.persistence.records import UserRoleCodeRecord
from backend.infrastructure.persistence.sqlalchemy.tables.role import (
    roles_table,
)
from backend.infrastructure.persistence.sqlalchemy.tables.role_permission import (
    user_roles_table,
)
from backend.infrastructure.tools.converters import CONVERTERS
from backend.infrastructure.tools.msgspec_tools import convert_record


def _value_to_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    if isinstance(value, (bytes, bytearray)):
        return UUID(bytes=bytes(value))
    return UUID(str(value))


def _decode_role(value: object) -> SystemRole:
    if isinstance(value, SystemRole):
        return value
    decoded = CONVERTERS.decode(value, SystemRole)
    if decoded is None:
        raise TypeError("role must not be None")
    return decoded


def _require_async_session(session: SessionProtocol) -> AsyncSession:
    if isinstance(session, AsyncSession):
        return session
    raise TypeError("SessionProtocol must be AsyncSession")


def q_get_user_role_codes(
    user_id: UUID,
) -> Callable[[SessionProtocol], Awaitable[list[UserRoleCodeRecord]]]:
    async def _q(session: SessionProtocol) -> list[UserRoleCodeRecord]:
        async_session = _require_async_session(session)
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
        rows = res.mappings().all()
        return [convert_record(dict(row), UserRoleCodeRecord) for row in rows]

    return _q


def q_get_role_ids_by_codes(
    codes: Sequence[SystemRole],
) -> Callable[[SessionProtocol], Awaitable[list[tuple[SystemRole, UUID]]]]:
    async def _q(session: SessionProtocol) -> list[tuple[SystemRole, UUID]]:
        async_session = _require_async_session(session)
        if not codes:
            return []
        stmt = sa.select(roles_table.c.code, roles_table.c.id).where(
            roles_table.c.code.in_(codes)
        )
        res = await async_session.execute(stmt)
        out: list[tuple[SystemRole, UUID]] = []
        for role_code, role_id in res.all():
            out.append((_decode_role(role_code), _value_to_uuid(role_id)))
        return out

    return _q


def q_replace_user_roles(
    user_id: UUID, role_ids: list[UUID]
) -> Callable[[SessionProtocol], Awaitable[None]]:
    async def _q(session: SessionProtocol) -> None:
        async_session = _require_async_session(session)
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
        async_session = _require_async_session(session)
        stmt = sa.select(user_roles_table.c.user_id).where(
            user_roles_table.c.role_id == role_id
        )
        res = await async_session.execute(stmt)
        return [_value_to_uuid(row[0]) for row in res.all()]

    return _q
