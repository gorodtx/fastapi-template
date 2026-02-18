from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import ColumnElement, FromClause, RowMapping

from backend.infrastructure.persistence.records import (
    UserRoleCodeRecord,
    UserRowRecord,
)
from backend.infrastructure.persistence.sqlalchemy.tables.role import (
    roles_table,
)
from backend.infrastructure.persistence.sqlalchemy.tables.role_permission import (
    role_permissions_table,
    user_roles_table,
)
from backend.infrastructure.persistence.sqlalchemy.tables.users import (
    users_table,
)
from backend.infrastructure.tools.msgspec_convert import convert_record

USER_ROW_COLUMNS = (
    users_table.c.id.label("id"),
    users_table.c.email.label("email"),
    users_table.c.login.label("login"),
    users_table.c.username.label("username"),
    users_table.c.password_hash.label("password_hash"),
    users_table.c.is_active.label("is_active"),
)

USER_ROLE_COLUMNS = (
    user_roles_table.c.user_id.label("user_id"),
    roles_table.c.code.label("role"),
)


def user_roles_join() -> FromClause:
    return user_roles_table.join(
        roles_table, user_roles_table.c.role_id == roles_table.c.id
    )


def user_permissions_join() -> FromClause:
    return user_roles_join().join(
        role_permissions_table,
        role_permissions_table.c.role_id == roles_table.c.id,
    )


def select_user_rows(
    where_clause: ColumnElement[bool],
) -> sa.Select[tuple]:
    return (
        sa.select(*USER_ROW_COLUMNS)
        .select_from(users_table)
        .where(where_clause)
    )


def select_user_roles(
    where_clause: ColumnElement[bool],
) -> sa.Select[tuple]:
    return (
        sa.select(*USER_ROLE_COLUMNS)
        .select_from(user_roles_join())
        .where(where_clause)
    )


def map_one_user_row(row: RowMapping | None) -> UserRowRecord | None:
    if row is None:
        return None
    return convert_record(dict(row), UserRowRecord)


def map_many_user_rows(rows: Sequence[RowMapping]) -> list[UserRowRecord]:
    return [convert_record(dict(row), UserRowRecord) for row in rows]


def map_many_user_role_rows(
    rows: Sequence[RowMapping],
) -> list[UserRoleCodeRecord]:
    return [convert_record(dict(row), UserRoleCodeRecord) for row in rows]
