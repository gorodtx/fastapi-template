from __future__ import annotations

from sqlalchemy import delete, insert, select

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.base import TypeID
from backend.domain.core.entities.user import User
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.password import Password
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
    _model_class = User

    async def create(self, user: User) -> User:
        self._session.add(user)
        await self._flush()
        await self._sync_user_roles(user=user)
        return user

    async def update(
        self,
        *,
        user_id: TypeID,
        email: Email | None,
        password: Password | None,
    ) -> User:
        user = await self._get_or_raise(user_id)
        await self._hydrate_user_roles(user)

        if email is not None:
            user.change_email(email)
        if password is not None:
            user.change_password(password)

        await self._flush()
        await self._sync_user_roles(user=user)
        return user

    async def delete(self, *, user_id: TypeID) -> User:
        user = await self._get_or_raise(user_id)

        await self._session.delete(user)
        await self._flush()

        return user

    async def get_one(self, *, user_id: TypeID) -> User:
        user = await self._get_or_raise(user_id)
        await self._hydrate_user_roles(user)
        return user

    async def _hydrate_user_roles(self, user: User) -> None:
        roles = await self._list_user_roles(user_id=user.id)
        user.hydrate_roles_for_persistence(roles)

    async def _list_user_roles(self, *, user_id: TypeID) -> set[SystemRole]:
        stmt = (
            select(role_code_column)
            .join(user_roles_table, role_id_column == user_roles_role_id_column)
            .where(user_roles_user_id_column == user_id)
        )
        result = await self._session.execute(stmt)
        return set(result.scalars().all())

    async def _sync_user_roles(self, *, user: User) -> None:
        desired_roles = set(user.roles)
        current_roles = await self._list_user_roles(user_id=user.id)
        if desired_roles == current_roles:
            return

        roles_to_add = desired_roles - current_roles
        roles_to_remove = current_roles - desired_roles
        if not roles_to_add and not roles_to_remove:
            return

        role_ids = await self._get_role_ids(roles_to_add | roles_to_remove)
        if roles_to_add:
            rows = [{"user_id": user.id, "role_id": role_ids[role]} for role in roles_to_add]
            await self._session.execute(insert(user_roles_table).values(rows))
        if roles_to_remove:
            role_ids_to_remove = [role_ids[role] for role in roles_to_remove]
            delete_stmt = delete(user_roles_table).where(
                user_roles_user_id_column == user.id,
                user_roles_role_id_column.in_(role_ids_to_remove),
            )
            await self._session.execute(delete_stmt)
        await self._flush()

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
