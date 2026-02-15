from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from uuid_utils.compat import UUID

from backend.infrastructure.persistence.adapters import users as users_adapter
from backend.infrastructure.persistence.adapters.users import SqlUsersAdapter
from backend.infrastructure.persistence.records import (
    UserRoleCodeRecord,
    UserRowRecord,
)

_ROWS_QUERY = object()
_ROLE_ROWS_QUERY = object()


def _password_hash(suffix: str) -> str:
    return "".join(("$argon2id$v=19$m=65536,t=3,p=4$abc$", suffix))


@dataclass(slots=True)
class _ManagerStub:
    rows: list[UserRowRecord]
    role_rows: list[UserRoleCodeRecord]
    seen_queries: list[object] = field(default_factory=list)

    async def send(self: _ManagerStub, query: object, /) -> object:
        self.seen_queries.append(query)
        if query is _ROWS_QUERY:
            return self.rows
        if query is _ROLE_ROWS_QUERY:
            return self.role_rows
        raise AssertionError("Unexpected query")


@pytest.mark.asyncio
async def test_get_by_ids_with_roles_uses_single_bulk_role_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_ids = [
        UUID("11111111-1111-1111-1111-111111111111"),
        UUID("22222222-2222-2222-2222-222222222222"),
    ]

    def _q_get_user_rows_by_ids(ids: list[UUID]) -> object:
        assert ids == user_ids
        return _ROWS_QUERY

    def _q_get_user_role_codes_by_user_ids(ids: list[UUID]) -> object:
        assert ids == user_ids
        return _ROLE_ROWS_QUERY

    def _q_get_user_role_codes(_user_id: UUID) -> object:
        raise AssertionError("Per-user role fetch should not be used")

    monkeypatch.setattr(
        users_adapter, "q_get_user_rows_by_ids", _q_get_user_rows_by_ids
    )
    monkeypatch.setattr(
        users_adapter,
        "q_get_user_role_codes_by_user_ids",
        _q_get_user_role_codes_by_user_ids,
    )
    monkeypatch.setattr(
        users_adapter, "q_get_user_role_codes", _q_get_user_role_codes
    )

    manager = _ManagerStub(
        rows=[
            UserRowRecord(
                id=user_ids[0],
                email="first@example.com",
                login="firstuser",
                username="firstuser",
                password_hash=_password_hash("def"),
                is_active=True,
            ),
            UserRowRecord(
                id=user_ids[1],
                email="second@example.com",
                login="seconduser",
                username="seconduser",
                password_hash=_password_hash("ghi"),
                is_active=True,
            ),
        ],
        role_rows=[
            UserRoleCodeRecord(user_id=user_ids[0], role="admin"),
            UserRoleCodeRecord(user_id=user_ids[0], role="user"),
            UserRoleCodeRecord(user_id=user_ids[1], role="user"),
        ],
    )
    adapter = SqlUsersAdapter(manager=manager)

    result = await adapter.get_by_ids(user_ids, include_roles=True)
    users = result.unwrap()

    assert manager.seen_queries == [_ROWS_QUERY, _ROLE_ROWS_QUERY]
    assert [user.id for user in users] == user_ids
    assert users[0].roles == {"admin", "user"}
    assert users[1].roles == {"user"}
