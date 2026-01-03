from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.base import TypeID
from backend.domain.core.entities.user import User
from backend.infrastructure.persistence.repositories.base import BaseRepository
from backend.infrastructure.persistence.sqlalchemy.models.role import (
    role_code_column,
    role_id_column,
)
from backend.infrastructure.persistence.sqlalchemy.models.role_permission import (
    user_roles_role_id_column,
    user_roles_table,
    user_roles_user_id_column,
)


class UsersRepo(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, entity=User)

    async def assign_role_to_user(self, *, user_id: TypeID, role: SystemRole) -> None:
        role_ids = await self._get_role_ids({role})
        role_id = role_ids[role]
        stmt = (
            pg_insert(user_roles_table)
            .values({"user_id": user_id, "role_id": role_id})
            .on_conflict_do_nothing(
                index_elements=[user_roles_user_id_column, user_roles_role_id_column]
            )
        )
        await self._session.execute(stmt)

    async def revoke_role_from_user(self, *, user_id: TypeID, role: SystemRole) -> None:
        role_ids = await self._get_role_ids({role})
        role_id = role_ids[role]
        stmt = delete(user_roles_table).where(
            user_roles_user_id_column == user_id,
            user_roles_role_id_column == role_id,
        )
        await self._session.execute(stmt)

    async def get_user_roles(self, *, user_id: TypeID) -> set[SystemRole]:
        stmt = (
            select(role_code_column)
            .join(user_roles_table, role_id_column == user_roles_role_id_column)
            .where(user_roles_user_id_column == user_id)
        )
        result = await self._session.execute(stmt)
        return set(result.scalars().all())

    async def list_user_ids_by_role(self, *, role: SystemRole) -> list[TypeID]:
        role_ids = await self._get_role_ids({role})
        role_id = role_ids[role]
        stmt = select(user_roles_user_id_column).where(user_roles_role_id_column == role_id)
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    async def _get_role_ids(self, roles: set[SystemRole]) -> dict[SystemRole, TypeID]:
        if not roles:
            return {}

        stmt = select(role_code_column, role_id_column).where(role_code_column.in_(roles))
        result = await self._session.execute(stmt)
        rows = result.all()
        mapping: dict[SystemRole, TypeID] = {}
        for role, role_id in rows:
            mapping[role] = role_id
        missing = roles - set(mapping)
        if missing:
            missing_values = ", ".join(sorted(role.value for role in missing))
            raise LookupError(f"System roles not found in database: {missing_values}")
        return mapping
