from __future__ import annotations

from dataclasses import field
from typing import Any

from fastapi_backend.domain.core.entities.base import Entity, TypeID, entity
from fastapi_backend.domain.core.exceptions.base import CorruptedInvariantError, DomainError
from fastapi_backend.domain.core.value_objects.email import Email
from fastapi_backend.domain.core.value_objects.login import Login
from fastapi_backend.domain.core.value_objects.password import Password
from fastapi_backend.domain.core.value_objects.username import Username
from fastapi_backend.domain.events.user.email_changed import UserEmailChanged
from fastapi_backend.domain.events.user.password_changed import UserPasswordChanged
from fastapi_backend.domain.events.user.registered import UserRegistered
from fastapi_backend.domain.events.user.username_changed import UserUsernameChanged


@entity
class User(Entity):
    id: TypeID
    email: Email
    login: Login
    username: Username
    password: Password = field(repr=False)

    @staticmethod
    def register(
        id: TypeID, email: Email, login: Login, username: Username, password: Password
    ) -> User:
        user = User(id=id, email=email, login=login, username=username, password=password)
        user._raise_event(
            UserRegistered(
                aggregate_id=user.id,
                username=username.value,
                email=email.value,
                login=login.value,
            )
        )
        return user

    def change_email(self, new_email: Email) -> None:
        if new_email.value == self.email.value:
            raise DomainError(f"New email {new_email.value!r} is same as current")

        old_value = self.email.value
        self.email = new_email  # type: ignore
        self._raise_event(
            UserEmailChanged(
                aggregate_id=self.id,
                old_email=old_value,
                new_email=new_email.value,
            )
        )

    def change_username(self, new_username: Username) -> None:
        if new_username.value == self.username.value:
            raise DomainError(f"New username {new_username.value!r} is same as current")

        old_value = self.username.value
        self.username = new_username  # type: ignore
        self._raise_event(
            UserUsernameChanged(
                aggregate_id=self.id,
                old_username=old_value,
                new_username=new_username.value,
            )
        )

    def change_password(self, new_password: Password) -> None:
        if new_password.value == self.password.value:
            raise DomainError("New password must differ from the old one")

        self.password = new_password  # type: ignore
        self._raise_event(UserPasswordChanged(aggregate_id=self.id))

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
