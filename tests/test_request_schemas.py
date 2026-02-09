from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.presentation.http.api.schemas.rbac import RoleChangeRequest
from backend.presentation.http.api.schemas.users import UserUpdateRequest


def _has_field_error(exc: ValidationError, field_name: str) -> bool:
    for error in exc.errors():
        loc = error.get("loc")
        if field_name == "" and isinstance(loc, tuple) and len(loc) == 0:
            return True
        if isinstance(loc, tuple) and loc and loc[0] == field_name:
            return True
    return False


def test_role_change_request_rejects_unknown_role() -> None:
    with pytest.raises(ValidationError) as exc_info:
        RoleChangeRequest(role_code="Unknown")

    assert _has_field_error(exc_info.value, "role_code")


def test_role_change_request_accepts_known_role() -> None:
    payload = RoleChangeRequest(role_code="user")

    assert payload.role_code == "user"


def test_user_update_request_rejects_empty_payload() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserUpdateRequest()

    assert _has_field_error(exc_info.value, "")


def test_user_update_request_accepts_non_empty_payload() -> None:
    payload = UserUpdateRequest(email="user@example.com")

    assert payload.email == "user@example.com"
