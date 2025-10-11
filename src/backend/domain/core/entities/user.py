from __future__ import annotations

from dataclasses import field
from typing import Any

from backend.domain.core.entities.base import Entity, TypeID, entity
from backend.domain.core.exceptions.base import CorruptedInvariantError, DomainError
from backend.domain.core.value_objects.email import Email
from backend.domain.core.value_objects.login import Login
from backend.domain.core.value_objects.password import Password
from backend.domain.core.value_objects.username import Username


@entity
class User(Entity):
    id: TypeID
    email: Email
    login: Login
    username: Username
    password: Password = field(repr=False)

    def change_email(self, new_email: Email) -> None:
        if new_email.value == self.email.value:
            raise DomainError(f"New email {new_email.value!r} is same as current")
        self.email = new_email  # type: ignore

    def change_username(self, new_username: Username) -> None:
        if new_username.value == self.username.value:
            raise DomainError(f"New username {new_username.value!r} is same as current")
        self.username = new_username  # type: ignore

    def change_password(self, new_password: Password) -> None:
        if new_password.value == self.password.value:
            raise DomainError("New password must differ from the old one")
        self.password = new_password  # type: ignore

    def ensure_invariants(self) -> None:
        if not isinstance(self.id, TypeID):
            raise CorruptedInvariantError(f"User id is invalid: {self.id!r}")

    def asdict(self) -> dict[str, Any]:
        data = super().asdict()
        data["email"] = self.email.value
        data["login"] = self.login.value
        data["username"] = self.username.value
        data.pop("password", None)
        return data
