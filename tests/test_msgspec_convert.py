from __future__ import annotations

import msgspec
import pytest
from uuid_utils.compat import UUID

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
