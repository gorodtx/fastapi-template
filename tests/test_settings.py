from __future__ import annotations

import pytest
from environs import Env

from backend.presentation.settings import Settings


def _load_settings(
    monkeypatch: pytest.MonkeyPatch, /, **overrides: str
) -> Settings:
    base: dict[str, str] = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@db:5432/app",
        "JWT_ISSUER": "issuer",
        "JWT_AUDIENCE": "audience",
        "JWT_ALG": "HS256",
        "JWT_SECRET": "secret",
        "JWT_ACCESS_TTL_S": "900",
        "JWT_REFRESH_TTL_S": "2592000",
        "AUTH_USER_CACHE_TTL_S": "300",
        "REFRESH_LOCK_TTL_S": "10.0",
        "REFRESH_LOCK_WAIT_TIMEOUT_S": "1.0",
    }
    base.update(overrides)

    for key, value in base.items():
        monkeypatch.setenv(key, value)

    return Settings.from_env(Env())


def test_settings_accepts_positive_security_timeouts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _load_settings(monkeypatch)
    assert settings.jwt_access_ttl_s == 900
    assert settings.jwt_refresh_ttl_s == 2592000
    assert settings.refresh_lock_ttl_s == 10.0
    assert settings.refresh_lock_wait_timeout_s == 1.0


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("JWT_ACCESS_TTL_S", "0"),
        ("JWT_REFRESH_TTL_S", "-1"),
    ],
)
def test_settings_rejects_non_positive_jwt_ttls(
    monkeypatch: pytest.MonkeyPatch, key: str, value: str
) -> None:
    with pytest.raises(RuntimeError, match=key):
        _load_settings(monkeypatch, **{key: value})


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("REFRESH_LOCK_TTL_S", "0"),
        ("REFRESH_LOCK_WAIT_TIMEOUT_S", "-0.1"),
    ],
)
def test_settings_rejects_non_positive_refresh_lock_values(
    monkeypatch: pytest.MonkeyPatch, key: str, value: str
) -> None:
    with pytest.raises(RuntimeError, match=key):
        _load_settings(monkeypatch, **{key: value})
