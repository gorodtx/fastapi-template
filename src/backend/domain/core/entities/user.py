from __future__ import annotations

from uuid_utils.compat import UUID

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.base import Entity, entity
from backend.domain.core.exceptions.rbac import RoleNotAssignedError
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.domain.core.value_objects.password import Password


@entity
class User(Entity):
    _email: Email
    _login: Login
    _username: Username
    _password: Password
    _is_active: bool
    _roles: set[SystemRole]

    def __init__(
        self: User,
        *,
        id: UUID,
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
    def email(self: User) -> Email:
        return self._email

    @property
    def login(self: User) -> Login:
        return self._login

    @property
    def username(self: User) -> Username:
        return self._username

    @property
    def password(self: User) -> Password:
        return self._password

    @property
    def is_active(self: User) -> bool:
        return self._is_active

    @property
    def roles(self: User) -> frozenset[SystemRole]:
        return frozenset(self._roles)

    @classmethod
    def register(
        cls: type[User],
        *,
        id: UUID,
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

    @classmethod
    def rehydrate(
        cls: type[User],
        *,
        id: UUID,
        email: Email,
        login: Login,
        username: Username,
        password: Password,
        is_active: bool,
        roles: set[SystemRole],
    ) -> User:
        return cls(
            id=id,
            email=email,
            login=login,
            username=username,
            password=password,
            is_active=is_active,
            roles=roles,
        )

    def assign_role(self: User, role: SystemRole) -> None:
        if role in self._roles:
            return
        self._roles.add(role)

    def revoke_role(self: User, role: SystemRole) -> None:
        if role not in self._roles:
            raise RoleNotAssignedError(role=role, user_id=self.id)
        self._roles.remove(role)
