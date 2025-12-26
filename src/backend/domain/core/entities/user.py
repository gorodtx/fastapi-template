from __future__ import annotations

from dataclasses import field

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.base import Entity, TypeID, entity
from backend.domain.core.exceptions.base import DomainError
from backend.domain.core.exceptions.rbac import RoleNotAssignedError
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.domain.core.value_objects.password import Password


@entity
class User(Entity):
    _email: Email = field(init=False, repr=False)
    _login: Login = field(init=False, repr=False)
    _username: Username = field(init=False, repr=False)
    _password: Password = field(init=False, repr=False)
    _is_active: bool = field(init=False, repr=False)
    _roles: set[SystemRole] = field(init=False, repr=False)

    def __init__(
        self,
        *,
        id: TypeID,
        email: Email,
        login: Login,
        username: Username,
        password: Password,
        is_active: bool = True,
        roles: set[SystemRole] | None = None,
    ) -> None:
        super().__init__(id=id)
        self._email = email
        self._login = login
        self._username = username
        self._password = password
        self._is_active = is_active
        self._roles = set(roles) if roles is not None else set()

    @property
    def email(self) -> Email:
        return self._email

    @property
    def login(self) -> Login:
        return self._login

    @property
    def username(self) -> Username:
        return self._username

    @property
    def password(self) -> Password:
        return self._password

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def roles(self) -> frozenset[SystemRole]:
        return frozenset(self._roles)

    @classmethod
    def register(
        cls,
        *,
        id: TypeID,
        email: Email,
        login: Login,
        username: Username,
        password: Password,
    ) -> User:
        return cls(
            id=id,
            email=email,
            login=login,
            username=username,
            password=password,
        )

    def change_email(self, new_email: Email) -> None:
        if new_email == self._email:
            raise DomainError(f"New email {new_email.value!r} is same as current")

        self._email = new_email

    def change_login(self, new_login: Login) -> None:
        if new_login == self._login:
            raise DomainError(f"New login {new_login.value!r} is same as current")

        self._login = new_login

    def change_username(self, new_username: Username) -> None:
        if new_username == self._username:
            raise DomainError(f"New username {new_username.value!r} is same as current")

        self._username = new_username

    def change_password(self, new_password: Password) -> None:
        if new_password == self._password:
            raise DomainError("New password must differ from the old one")

        self._password = new_password

    def activate(self) -> None:
        if self._is_active:
            return
        self._is_active = True

    def deactivate(self) -> None:
        if not self._is_active:
            return
        self._is_active = False

    def assign_role(self, role: SystemRole) -> None:
        if role in self._roles:
            return
        self._roles.add(role)

    def revoke_role(self, role: SystemRole) -> None:
        if role not in self._roles:
            raise RoleNotAssignedError(role=role, user_id=self.id)
        self._roles.remove(role)

    def has_role(self, role: SystemRole) -> bool:
        return role in self._roles

    def hydrate_roles_for_persistence(self, roles: set[SystemRole]) -> None:
        self._roles = set(roles)
