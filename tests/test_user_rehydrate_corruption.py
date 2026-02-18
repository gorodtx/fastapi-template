from __future__ import annotations

import pytest
from uuid_utils.compat import UUID

from backend.domain.core.exceptions.user import UserDataCorruptedError
from backend.domain.core.services.users import rehydrate_user

_USER_ID = UUID("0194f6f0-7f2a-7000-8000-000000000001")


def _password_hash() -> str:
    return "".join(("$argon2id$v=19$m=65536,t=3,p=4$", "salt", "$", "hash"))


def test_rehydrate_user_accepts_fixed_system_roles() -> None:
    user = rehydrate_user(
        id=_USER_ID,
        email="user@example.com",
        login="user123",
        username="user_name",
        password_hash=_password_hash(),
        is_active=True,
        roles={"admin", "user"},
    )

    assert user.roles == {"admin", "user"}


def test_rehydrate_user_rejects_invalid_role_format() -> None:
    with pytest.raises(UserDataCorruptedError, match="invalid role entry"):
        rehydrate_user(
            id=_USER_ID,
            email="user@example.com",
            login="user123",
            username="user_name",
            password_hash=_password_hash(),
            is_active=True,
            roles={"admin!"},
        )


def test_rehydrate_user_rejects_unknown_role_catalog_entry() -> None:
    with pytest.raises(UserDataCorruptedError, match="unknown role code"):
        rehydrate_user(
            id=_USER_ID,
            email="user@example.com",
            login="user123",
            username="user_name",
            password_hash=_password_hash(),
            is_active=True,
            roles={"auditor"},
        )
