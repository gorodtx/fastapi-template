from __future__ import annotations

import msgspec
import pytest
from uuid_utils.compat import UUID

from backend.domain.core.constants.rbac import SystemRole
from backend.infrastructure.persistence.records import UserRowRecord
from backend.infrastructure.tools.msgspec_convert import convert_record


def _base_row() -> dict[str, object]:
    return {
        "id": UUID("11111111-1111-1111-1111-111111111111"),
        "email": "user@example.com",
        "login": "user123",
        "username": "user123",
        "password_hash": "".join(
            ("$argon2id$v=19$m=65536,t=3,p=4$abc$", "def")
        ),
    }


def test_convert_record_accepts_boolean_is_active() -> None:
    row = {**_base_row(), "is_active": True}

    record = convert_record(row, UserRowRecord)

    assert record.is_active is True


def test_convert_record_rejects_string_boolean_is_active() -> None:
    row = {**_base_row(), "is_active": "false"}

    with pytest.raises(msgspec.ValidationError):
        convert_record(row, UserRowRecord)


def test_convert_record_rejects_int_boolean_is_active() -> None:
    row = {**_base_row(), "is_active": 1}

    with pytest.raises(msgspec.ValidationError):
        convert_record(row, UserRowRecord)


class _RoleRecord(msgspec.Struct, frozen=True):
    role: SystemRole


def test_convert_record_decodes_system_role_without_app_startup() -> None:
    record = convert_record({"role": "admin"}, _RoleRecord)

    assert record.role is SystemRole.ADMIN


def test_convert_record_encodes_system_role_to_string_field() -> None:
    record = convert_record(
        {"role": SystemRole.SUPER_ADMIN},
        _StringRoleRecord,
    )

    assert record.role == "super_admin"


class _StringRoleRecord(msgspec.Struct, frozen=True):
    role: str
