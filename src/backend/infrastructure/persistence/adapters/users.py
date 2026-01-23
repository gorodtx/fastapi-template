from __future__ import annotations

from uuid_utils.compat import UUID

from backend.application.common.exceptions.storage import StorageError
from backend.application.common.interfaces.ports.persistence.users_adapter import UsersAdapter
from backend.application.handlers.result import Result
from backend.domain.core.entities.user import User
from backend.infrastructure.persistence.adapters.base import UnboundAdapter
from backend.infrastructure.persistence.mappers.users import (
    role_records_to_set,
    row_record_to_user,
    user_to_row_record,
)
from backend.infrastructure.persistence.rawrepo.rbac import q_get_user_role_codes
from backend.infrastructure.persistence.rawrepo.users import (
    q_delete_user,
    q_get_user_row_by_id,
    q_upsert_user_row,
)
from backend.infrastructure.tools.as_result import as_result


class SqlUsersAdapter(UnboundAdapter, UsersAdapter):
    __slots__ = ()

    @as_result()
    async def get_by_id(self, user_id: UUID) -> User:
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

    @as_result()
    async def save(self, user: User) -> User:
        row = user_to_row_record(user)
        saved_row = await self.manager.send(q_upsert_user_row(row))
        role_rows = await self.manager.send(q_get_user_role_codes(user.id))
        roles = role_records_to_set(role_rows)
        return row_record_to_user(saved_row, roles=roles)

    @as_result()
    async def delete(self, user_id: UUID) -> bool:
        return await self.manager.send(q_delete_user(user_id))


__all__ = ["Result", "SqlUsersAdapter", "StorageError", "UsersAdapter"]
