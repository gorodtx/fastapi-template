from __future__ import annotations

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.user import User
from backend.domain.core.factories.users import UserFactory
from backend.infrastructure.persistence.records import (
    UserRoleCodeRecord,
    UserRowRecord,
)
from backend.infrastructure.tools.converters import CONVERTERS


def user_to_row_record(user: User) -> UserRowRecord:
    email = CONVERTERS.encode(user.email)
    login = CONVERTERS.encode(user.login)
    username = CONVERTERS.encode(user.username)
    password_hash = CONVERTERS.encode(user.password)

    if not isinstance(email, str):
        raise TypeError("Email encoding must return str")
    if not isinstance(login, str):
        raise TypeError("Login encoding must return str")
    if not isinstance(username, str):
        raise TypeError("Username encoding must return str")
    if not isinstance(password_hash, str):
        raise TypeError("Password encoding must return str")

    return UserRowRecord(
        id=user.id,
        email=email,
        login=login,
        username=username,
        password_hash=password_hash,
        is_active=user.is_active,
    )


def row_record_to_user(
    rec: UserRowRecord,
    *,
    roles: set[SystemRole] | None = None,
) -> User:
    return UserFactory.rehydrate(
        id=rec.id,
        email=rec.email,
        login=rec.login,
        username=rec.username,
        password_hash=rec.password_hash,
        is_active=rec.is_active,
        roles=roles or set(),
    )


def role_records_to_set(records: list[UserRoleCodeRecord]) -> set[SystemRole]:
    return {SystemRole(record.role) for record in records}
