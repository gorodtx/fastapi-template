from __future__ import annotations

from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.application.common.exceptions.storage import StorageError
from backend.application.common.interfaces.ports.persistence.rbac_adapter import (
    RbacAdapter,
)
from backend.application.handlers.result import Result
from backend.domain.core.types.rbac import (
    PermissionCode,
    RoleCode,
)
from backend.infrastructure.persistence.adapters.base import UnboundAdapter
from backend.infrastructure.persistence.mappers.users import (
    role_records_to_set,
)
from backend.infrastructure.persistence.rawadapter.rbac import (
    q_get_role_ids_by_codes,
    q_get_user_permission_codes,
    q_get_user_role_codes,
    q_list_user_ids_by_role_id,
    q_replace_user_roles,
)
from backend.infrastructure.persistence.records import UserRoleCodeRecord
from backend.infrastructure.tools.storage_result import storage_result


@dataclass(frozen=True, slots=True)
class _ReplaceUserRoles:
    user_id: UUID
    roles: set[RoleCode]


class SqlRbacAdapter(UnboundAdapter, RbacAdapter):
    __slots__: tuple[str, ...] = ()

    async def get_user_roles(
        self: SqlRbacAdapter, user_id: UUID
    ) -> Result[set[RoleCode], StorageError]:
        async def _call() -> set[RoleCode]:
            rows: list[UserRoleCodeRecord] = await self.manager.send(
                q_get_user_role_codes(user_id)
            )
            return role_records_to_set(rows)

        return await storage_result(_call)

    async def get_user_permission_codes(
        self: SqlRbacAdapter, user_id: UUID
    ) -> Result[set[PermissionCode], StorageError]:
        async def _call() -> set[PermissionCode]:
            rows = await self.manager.send(
                q_get_user_permission_codes(user_id)
            )
            return {PermissionCode(row) for row in rows}

        return await storage_result(_call)

    async def replace_user_roles(
        self: SqlRbacAdapter, user_id: UUID, roles: set[RoleCode]
    ) -> Result[None, StorageError]:
        async def _call() -> None:
            payload = _ReplaceUserRoles(user_id=user_id, roles=roles)
            pairs = await self.manager.send(
                q_get_role_ids_by_codes(list(payload.roles))
            )
            got = {role for (role, _role_id) in pairs}
            want = set(payload.roles)
            missing = want - got
            if missing:
                raise StorageError(
                    code="rbac.seed_mismatch",
                    message="RBAC roles are missing in DB (seed mismatch)",
                )
            role_ids = [rid for (_role, rid) in pairs]
            await self.manager.send(
                q_replace_user_roles(payload.user_id, role_ids)
            )

        return await storage_result(_call)

    async def list_user_ids_by_role(
        self: SqlRbacAdapter, role: RoleCode
    ) -> Result[list[UUID], StorageError]:
        async def _call() -> list[UUID]:
            pairs = await self.manager.send(q_get_role_ids_by_codes([role]))
            if not pairs:
                raise StorageError(
                    code="rbac.seed_mismatch",
                    message="RBAC roles are missing in DB (seed mismatch)",
                )
            role_id = pairs[0][1]
            return await self.manager.send(q_list_user_ids_by_role_id(role_id))

        return await storage_result(_call)
