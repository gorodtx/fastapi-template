from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.engine import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.base import TypeID
from backend.infrastructure.persistence.sqlalchemy.models.role import (
    role_code_column,
    role_id_column,
    roles_table,
)
from backend.infrastructure.persistence.sqlalchemy.models.role_permission import (
    user_roles_role_id_column,
    user_roles_table,
    user_roles_user_id_column,
)


class RbacRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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

    async def count_users_with_role(self, *, role: SystemRole) -> int:
        stmt = (
            select(func.count())
            .select_from(
                user_roles_table.join(roles_table, role_id_column == user_roles_role_id_column)
            )
            .where(role_code_column == role)
        )
        result = await self._session.execute(stmt)
        count = result.scalar_one()
        return int(count)
