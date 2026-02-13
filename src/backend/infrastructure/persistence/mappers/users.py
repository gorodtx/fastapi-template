from __future__ import annotations

from backend.domain.core.entities.user import User
from backend.domain.core.services.users import rehydrate_user
from backend.domain.core.types.rbac import RoleCode
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
    return rehydrate_user(
        id=rec.id,
        email=rec.email,
        login=rec.login,
        username=rec.username,
        password_hash=rec.password_hash,
        is_active=rec.is_active,
        roles=roles or set(),
    )


def role_records_to_set(records: list[UserRoleCodeRecord]) -> set[RoleCode]:
    role_codes: set[RoleCode] = set()
    for record in records:
        role_codes.add(record.role)
    return role_codes
