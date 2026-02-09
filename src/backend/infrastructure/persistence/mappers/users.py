from __future__ import annotations

from backend.domain.core.entities.user import User
from backend.domain.core.value_objects.access.role_code import RoleCode
from backend.infrastructure.persistence.records import (
    UserRoleCodeRecord,
    UserRowRecord,
)


def user_to_row_record(user: User) -> UserRowRecord:
    return UserRowRecord(
        id=user.id,
        email=user.email,
        login=user.login,
        username=user.username,
        password_hash=user.password,
        is_active=user.is_active,
    )


def row_record_to_user(
    rec: UserRowRecord,
    *,
    roles: set[RoleCode] | None = None,
) -> User:
    return User.rehydrate(
        id=rec.id,
        email=rec.email,
        login=rec.login,
        username=rec.username,
        password=rec.password_hash,
        is_active=rec.is_active,
        roles=roles or set(),
    )


def role_records_to_set(records: list[UserRoleCodeRecord]) -> set[RoleCode]:
    return {RoleCode(record.role) for record in records}
