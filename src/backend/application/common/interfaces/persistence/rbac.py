from __future__ import annotations

from typing import Protocol

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.base import TypeID


class RbacPort(Protocol):
    async def assign_role_to_user(self, *, user_id: TypeID, role: SystemRole) -> None: ...

    async def revoke_role_from_user(self, *, user_id: TypeID, role: SystemRole) -> None: ...

    async def list_user_roles(self, *, user_id: TypeID) -> set[SystemRole]: ...
