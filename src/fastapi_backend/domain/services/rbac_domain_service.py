from __future__ import annotations

import uuid_utils.compat as uuid

from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.core.entities.role import Role
from fastapi_backend.domain.core.value_objects.access.permission_code import PermissionCode
from fastapi_backend.domain.core.value_objects.identity.role_name import RoleName
from fastapi_backend.domain.ports.event_dispatcher import EventDispatcherPort


class RBACDomainService:
    def __init__(self, event_dispatcher: EventDispatcherPort) -> None:
        self._event_dispatcher = event_dispatcher

    async def create_role(self, name: RoleName, description: str | None = None) -> Role:
        role = Role.create(id=uuid.uuid7(), name=name, description=description)
        events = role.pull_events()
        await self._event_dispatcher.publish(events)
        return role

    async def update_role(self, role: Role, name: RoleName, description: str | None = None) -> None:
        role.rename(name, description)
        events = role.pull_events()
        await self._event_dispatcher.publish(events)

    async def delete_role(self, role: Role) -> None:
        role.delete()
        events = role.pull_events()
        await self._event_dispatcher.publish(events)

    async def grant_permission(self, role: Role, perm: PermissionCode) -> None:
        role.grant(perm)
        events = role.pull_events()
        await self._event_dispatcher.publish(events)

    async def revoke_permission(self, role: Role, perm: PermissionCode) -> None:
        role.revoke(perm)
        events = role.pull_events()
        await self._event_dispatcher.publish(events)

    async def assign_role_to_user(self, role: Role, user_id: TypeID) -> None:
        role.assign_to_user(user_id)
        events = role.pull_events()
        await self._event_dispatcher.publish(events)

    async def revoke_role_from_user(self, role: Role, user_id: TypeID) -> None:
        role.revoke_from_user(user_id)
        events = role.pull_events()
        await self._event_dispatcher.publish(events)
