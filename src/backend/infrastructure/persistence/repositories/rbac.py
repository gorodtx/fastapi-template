from __future__ import annotations

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.base import TypeID
from backend.infrastructure.persistence.sqlalchemy.models.role import (
    role_code_column,
    role_id_column,
)
from backend.infrastructure.persistence.sqlalchemy.models.role_permission import (
    user_roles_role_id_column,
    user_roles_table,
    user_roles_user_id_column,
)


class RbacRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def assign_role_to_user(self, *, user_id: TypeID, role: SystemRole) -> None:
        role_id = await self._get_role_id(role)

        stmt = select(user_roles_role_id_column).where(
            user_roles_user_id_column == user_id,
            user_roles_role_id_column == role_id,
        )
        result = await self._session.execute(stmt)
        exists = result.scalar_one_or_none()
        if exists is not None:
            return

        insert_stmt = (
            insert(user_roles_table)
            .values(user_id=user_id, role_id=role_id)
            .returning(user_roles_role_id_column)
        )
        await self._session.execute(insert_stmt)
        await self._session.flush()

    async def revoke_role_from_user(self, *, user_id: TypeID, role: SystemRole) -> None:
        role_id = await self._get_role_id(role)

        delete_stmt = (
            delete(user_roles_table)
            .where(
                user_roles_user_id_column == user_id,
                user_roles_role_id_column == role_id,
            )
            .returning(user_roles_role_id_column)
        )
        await self._session.execute(delete_stmt)
        await self._session.flush()

    async def list_user_roles(self, *, user_id: TypeID) -> set[SystemRole]:
        stmt = (
            select(role_code_column)
            .join(user_roles_table, role_id_column == user_roles_role_id_column)
            .where(user_roles_user_id_column == user_id)
        )
        result = await self._session.execute(stmt)
        scalar_rows: ScalarResult[SystemRole] = result.scalars()
        rows = scalar_rows.all()
        return set(rows)

    async def _get_role_id(self, role: SystemRole) -> TypeID:
        stmt = select(role_id_column).where(role_code_column == role)
        result = await self._session.execute(stmt)
        role_id = result.scalar_one_or_none()
        if role_id is None:
            raise LookupError(f"System role {role.value!r} not found in database")
        return role_id
