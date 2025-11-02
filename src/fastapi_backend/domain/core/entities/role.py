from __future__ import annotations

from dataclasses import field

from fastapi_backend.domain.core.entities.base import Entity, TypeID, entity
from fastapi_backend.domain.core.value_objects.access.permission_code import PermissionCode
from fastapi_backend.domain.core.value_objects.identity.role_name import RoleName
from fastapi_backend.domain.events.rbac.create import RoleCreated
from fastapi_backend.domain.events.rbac.delete import RoleDeleted
from fastapi_backend.domain.events.rbac.permissions import (
    PermissionGrantedToRole,
    PermissionRevokedFromRole,
    UserRoleAssigned,
    UserRoleRevoked,
)
from fastapi_backend.domain.events.rbac.update import RoleUpdated


@entity
class Role(Entity):
    name: RoleName
    id: TypeID

    description: str | None = None
    permissions: set[PermissionCode] = field(default_factory=set)
    user_ids: set[TypeID] = field(default_factory=set)

    @staticmethod
    def create(id: TypeID, name: RoleName, description: str | None = None) -> Role:
        role = Role(id=id, name=name, description=description)
        role._raise_event(RoleCreated(aggregate_id=id, name=name.value))
        return role

    def rename(self, new_name: RoleName, description: str | None = None) -> None:
        changed = (new_name.value != self.name.value) or (description != self.description)
        if not changed:
            return
        self.name = new_name  # type: ignore
        self.description = description
        self._raise_event(RoleUpdated(aggregate_id=self.id, name=new_name.value))

    def grant(self, perm: PermissionCode) -> None:
        if perm in self.permissions:
            return
        self.permissions.add(perm)
        self._raise_event(PermissionGrantedToRole(aggregate_id=self.id, permission=perm.value))

    def revoke(self, perm: PermissionCode) -> None:
        if perm not in self.permissions:
            return
        self.permissions.remove(perm)
        self._raise_event(PermissionRevokedFromRole(aggregate_id=self.id, permission=perm.value))

    def assign_to_user(self, user_id: TypeID) -> None:
        if user_id in self.user_ids:
            return
        self.user_ids.add(user_id)
        self._raise_event(UserRoleAssigned(aggregate_id=self.id, user_id=user_id))

    def revoke_from_user(self, user_id: TypeID) -> None:
        if user_id not in self.user_ids:
            return
        self.user_ids.remove(user_id)
        self._raise_event(UserRoleRevoked(aggregate_id=self.id, user_id=user_id))

    def delete(self) -> None:
        self._raise_event(RoleDeleted(aggregate_id=self.id))
