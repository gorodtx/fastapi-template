from __future__ import annotations

from dataclasses import field

from backend.domain.core.entities.base import Entity, TypeID, entity
from backend.domain.core.exceptions.base import CorruptedInvariantError, DomainError
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.domain.core.value_objects.password import Password


@entity
class User(Entity):
    id: TypeID
    email: Email
    login: Login
    username: Username
    password: Password = field(repr=False)
    role_ids: set[TypeID] = field(default_factory=set)

    @staticmethod
    def register(
        id: TypeID,
        email: Email,
        login: Login,
        username: Username,
        password: Password,
    ) -> User:
        user = User(
            id=id,
            email=email,
            login=login,
            username=username,
            password=password,
        )
        return user

    def change_email(self, new_email: Email) -> None:
        if new_email.value == self.email.value:
            raise DomainError(f"New email {new_email.value!r} is same as current")

        self.email = new_email  # type: ignore[misc]

    def change_username(self, new_username: Username) -> None:
        if new_username.value == self.username.value:
            raise DomainError(f"New username {new_username.value!r} is same as current")

        self.username = new_username  # type: ignore[misc]

    def change_password(self, new_password: Password) -> None:
        if new_password.value == self.password.value:
            raise DomainError("New password must differ from the old one")

        self.password = new_password  # type: ignore[misc]

    def assign_role(self, role_id: TypeID) -> None:
        if role_id in self.role_ids:
            return
        self.role_ids.add(role_id)

    def revoke_role(self, role_id: TypeID) -> None:
        if role_id not in self.role_ids:
            return
        self.role_ids.remove(role_id)

    def ensure_invariants(self) -> None:
        if not isinstance(self.id, TypeID):
            raise CorruptedInvariantError(f"User id is invalid: {self.id!r}")
