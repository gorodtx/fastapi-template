from __future__ import annotations

from typing import Protocol

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.base import TypeID


class RbacPort(Protocol):
    async def list_user_roles(self, *, user_id: TypeID) -> set[SystemRole]: ...

    async def count_users_with_role(self, *, role: SystemRole) -> int: ...
