from __future__ import annotations

from dataclasses import field

from backend.domain.core.entities.base import Entity, TypeID, entity
from backend.domain.core.value_objects.access.permission_code import PermissionCode
from backend.domain.core.value_objects.identity.role_name import RoleName


@entity
class Role(Entity):
    id: TypeID
    name: RoleName
    permissions: set[PermissionCode] = field(default_factory=set)

    @staticmethod
    def create(id: TypeID, name: RoleName) -> Role:
        role = Role(id=id, name=name)
        return role

    def rename(self, new_name: RoleName) -> None:
        if new_name.value == self.name.value:
            return
        self.name = new_name  # type: ignore[misc]

    def grant(self, perm: PermissionCode) -> None:
        if perm in self.permissions:
            return
        self.permissions.add(perm)

    def revoke(self, perm: PermissionCode) -> None:
        if perm not in self.permissions:
            return
        self.permissions.remove(perm)

    def delete(self) -> None: ...
