from __future__ import annotations

import pytest

from backend.domain.core.value_objects.identity.login import Login


def test_login_accepts_valid_value() -> None:
    login = Login("abc123")
    assert login.value == "abc123"


def test_login_rejects_too_short_value() -> None:
    with pytest.raises(ValueError):
        Login("ab")


def test_login_rejects_non_alnum_value() -> None:
    with pytest.raises(ValueError):
        Login("abc-123")
