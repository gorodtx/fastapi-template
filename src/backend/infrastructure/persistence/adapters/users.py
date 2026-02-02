from __future__ import annotations

from uuid_utils.compat import UUID

from backend.application.common.exceptions.storage import StorageError
from backend.application.common.interfaces.ports.persistence.users_adapter import (
    UsersAdapter,
)
from backend.application.handlers.result import Result
from backend.domain.core.entities.user import User
from backend.infrastructure.persistence.adapters.base import UnboundAdapter
from backend.infrastructure.persistence.mappers.users import (
    role_records_to_set,
    row_record_to_user,
    user_to_row_record,
)
from backend.infrastructure.persistence.rawadapter.rbac import (
    q_get_user_role_codes,
)
from backend.infrastructure.persistence.rawadapter.users import (
    q_delete_user,
    q_get_user_row_by_email,
    q_get_user_row_by_id,
    q_upsert_user_row,
)
from backend.infrastructure.tools.storage_result import storage_result


class SqlUsersAdapter(UnboundAdapter, UsersAdapter):
    __slots__: tuple[str, ...] = ()

    async def get_by_id(
        self: SqlUsersAdapter, user_id: UUID
    ) -> Result[User, StorageError]:
        async def _call() -> User:
            rec = await self.manager.send(q_get_user_row_by_id(user_id))
            rec = self.require_found(
                rec,
                code="user.not_found",
                message="User not found",
                detail=f"id={user_id}",
            )
            role_rows = await self.manager.send(q_get_user_role_codes(user_id))
            roles = role_records_to_set(role_rows)
            return row_record_to_user(rec, roles=roles)

        return await storage_result(_call)

    async def get_by_email(
        self: SqlUsersAdapter, email: str
    ) -> Result[User, StorageError]:
        async def _call() -> User:
            rec = await self.manager.send(q_get_user_row_by_email(email))
            rec = self.require_found(
                rec,
                code="user.not_found",
                message="User not found",
                detail=f"email={email}",
            )
            role_rows = await self.manager.send(q_get_user_role_codes(rec.id))
            roles = role_records_to_set(role_rows)
            return row_record_to_user(rec, roles=roles)

        return await storage_result(_call)

    async def save(
        self: SqlUsersAdapter, user: User
    ) -> Result[User, StorageError]:
        async def _call() -> User:
            row = user_to_row_record(user)
            saved_row = await self.manager.send(q_upsert_user_row(row))
            role_rows = await self.manager.send(q_get_user_role_codes(user.id))
            roles = role_records_to_set(role_rows)
            return row_record_to_user(saved_row, roles=roles)

        return await storage_result(_call)

    async def delete(
        self: SqlUsersAdapter, user_id: UUID
    ) -> Result[bool, StorageError]:
        async def _call() -> bool:
            return await self.manager.send(q_delete_user(user_id))

        return await storage_result(_call)
