from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.presentation.http.api.schemas.auth import LoginRequest


def _has_field_error(exc: ValidationError, field_name: str) -> bool:
    for error in exc.errors():
        loc = error.get("loc")
        if isinstance(loc, tuple) and loc and loc[0] == field_name:
            return True
    return False


def _build_raw_password() -> str:
    return "".join(("valid", "-", "password", "-", "value"))


def test_login_request_accepts_valid_payload() -> None:
    raw_password = _build_raw_password()
    payload = LoginRequest(
        email="valid@example.com",
        raw_password=raw_password,
        fingerprint="fp-12345678",
    )

    assert payload.email == "valid@example.com"
    assert payload.raw_password == raw_password
    assert payload.fingerprint == "fp-12345678"


def test_login_request_rejects_invalid_email() -> None:
    raw_password = _build_raw_password()
    with pytest.raises(ValidationError) as exc_info:
        LoginRequest(
            email="bad-email",
            raw_password=raw_password,
            fingerprint="fp-12345678",
        )

    assert _has_field_error(exc_info.value, "email")


@pytest.mark.parametrize(
    ("field_name", "raw_password", "fingerprint"),
    (
        ("raw_password", "", "fp-12345678"),
        ("fingerprint", _build_raw_password(), "short"),
        ("fingerprint", _build_raw_password(), "fp with spaces"),
    ),
)
def test_login_request_rejects_invalid_fields(
    field_name: str,
    raw_password: str,
    fingerprint: str,
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        LoginRequest(
            email="valid@example.com",
            raw_password=raw_password,
            fingerprint=fingerprint,
        )

    assert _has_field_error(exc_info.value, field_name)
