from __future__ import annotations

import pytest

from backend.domain.core.policies.identity import (
    validate_email,
    validate_fingerprint,
    validate_login,
    validate_password_hash,
    validate_username,
)
from backend.domain.core.policies.rbac import validate_role_code


def test_validate_login_accepts_alnum_between_3_and_20() -> None:
    assert validate_login("abc123") == "abc123"
    assert validate_login("A1B2C3") == "A1B2C3"


@pytest.mark.parametrize("bad_login", ("ab", "login-with-dash", "with space"))
def test_validate_login_rejects_invalid_values(bad_login: str) -> None:
    with pytest.raises(ValueError):
        validate_login(bad_login)


def test_validate_email_accepts_standard_format() -> None:
    assert (
        validate_email("User.Name+tag@example.com")
        == "User.Name+tag@example.com"
    )


def test_validate_fingerprint_accepts_supported_chars() -> None:
    assert validate_fingerprint("fp-1234_ABC.def:zzz") == "fp-1234_ABC.def:zzz"


@pytest.mark.parametrize(
    "bad_fingerprint",
    ("short", "has space", "x" * 129),
)
def test_validate_fingerprint_rejects_invalid_values(
    bad_fingerprint: str,
) -> None:
    with pytest.raises(ValueError):
        validate_fingerprint(bad_fingerprint)


def test_validate_username_rejects_whitespace() -> None:
    with pytest.raises(ValueError):
        validate_username("bad user")


def test_validate_password_hash_requires_phc_prefix() -> None:
    with pytest.raises(ValueError):
        validate_password_hash("plain-text-password")


def test_validate_role_code_accepts_lower_snake_case() -> None:
    assert validate_role_code("super_admin") == "super_admin"
