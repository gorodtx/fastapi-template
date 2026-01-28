from __future__ import annotations

from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.application.common.exceptions.storage import StorageError
from backend.application.common.interfaces.ports.persistence.rbac_adapter import (
    RbacAdapter,
)
from backend.application.handlers.result import Result
from backend.domain.core.constants.rbac import SystemRole
from backend.infrastructure.persistence.adapters.base import UnboundAdapter
from backend.infrastructure.persistence.mappers.users import (
    role_records_to_set,
)
from backend.infrastructure.persistence.rawadapter.rbac import (
    q_get_role_ids_by_codes,
    q_get_user_role_codes,
    q_list_user_ids_by_role_id,
    q_replace_user_roles,
)
from backend.infrastructure.persistence.records import UserRoleCodeRecord
from backend.infrastructure.tools import storage_result


@dataclass(frozen=True, slots=True)
class _ReplaceUserRoles:
    user_id: UUID
    roles: set[SystemRole]


class SqlRbacAdapter(UnboundAdapter, RbacAdapter):
    __slots__: tuple[str, ...] = ()

    async def get_user_roles(
        self: SqlRbacAdapter, user_id: UUID
    ) -> Result[set[SystemRole], StorageError]:
        async def _call() -> set[SystemRole]:
            rows: list[UserRoleCodeRecord] = await self.manager.send(
                q_get_user_role_codes(user_id)
            )
            return role_records_to_set(rows)

        return await storage_result(_call)

    async def replace_user_roles(
        self: SqlRbacAdapter, user_id: UUID, roles: set[SystemRole]
    ) -> Result[None, StorageError]:
        async def _call() -> None:
            payload = _ReplaceUserRoles(user_id=user_id, roles=roles)
            pairs = await self.manager.send(
                q_get_role_ids_by_codes(list(payload.roles))
            )
            got = {role.value for (role, _role_id) in pairs}
            want = {role.value for role in payload.roles}
            missing = want - got
            if missing:
                raise StorageError(
                    code="rbac.seed_mismatch",
                    message="RBAC roles are missing in DB (seed mismatch)",
                    detail=f"missing={sorted(missing)}",
                )
            role_ids = [rid for (_role, rid) in pairs]
            await self.manager.send(
                q_replace_user_roles(payload.user_id, role_ids)
            )

        return await storage_result(_call)

    async def list_user_ids_by_role(
        self: SqlRbacAdapter, role: SystemRole
    ) -> Result[list[UUID], StorageError]:
        async def _call() -> list[UUID]:
            pairs = await self.manager.send(q_get_role_ids_by_codes([role]))
            if not pairs:
                raise StorageError(
                    code="rbac.seed_mismatch",
                    message="RBAC roles are missing in DB (seed mismatch)",
                    detail=f"missing={[role.value]}",
                )
            role_id = pairs[0][1]
            return await self.manager.send(q_list_user_ids_by_role_id(role_id))

        return await storage_result(_call)
