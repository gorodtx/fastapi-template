from __future__ import annotations

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.constants.serialization import encode_str
from backend.domain.core.entities.user import User
from backend.domain.core.factories.users import UserFactory
from backend.infrastructure.persistence.records import (
    UserRoleCodeRecord,
    UserRowRecord,
)


def user_to_row_record(user: User) -> UserRowRecord:
    email = encode_str(user.email)
    login = encode_str(user.login)
    username = encode_str(user.username)
    password_hash = encode_str(user.password)

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
