from __future__ import annotations

import pytest
from environs import Env

from backend.presentation.settings import Settings


def _load_settings(
    monkeypatch: pytest.MonkeyPatch, /, **overrides: str
) -> Settings:
    base: dict[str, str] = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@pgbouncer:5432/app",
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
    assert settings.obs_otel_enabled is False
    assert settings.obs_otel_service_name == "backend"
    assert settings.obs_otel_service_version == "0.1.0"
    assert settings.obs_otel_environment == "dev"
    assert settings.obs_otel_exporter_otlp_endpoint is None
    assert settings.obs_otel_exporter_otlp_headers is None
    assert settings.obs_otel_exporter_otlp_ca_cert_file is None
    assert settings.obs_otel_exporter_otlp_client_cert_file is None
    assert settings.obs_otel_exporter_otlp_client_key_file is None
    assert settings.obs_otel_metrics_export_interval_ms == 15000
    assert settings.app_instance_count == 1
    assert settings.pgbouncer_max_client_conn == 500
    assert settings.pgbouncer_default_pool_size == 50
    assert settings.pgbouncer_reserve_pool_size == 10
    assert settings.pgbouncer_max_db_connections == 100
    assert settings.postgres_max_connections is None
    assert settings.postgres_superuser_reserved_connections is None


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


def test_settings_rejects_non_pgbouncer_database_url_in_dev(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        _load_settings(
            monkeypatch,
            DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/app",
        )


def test_settings_allows_non_pgbouncer_database_url_in_test_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _load_settings(
        monkeypatch,
        APP_ENV="test",
        DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/app",
    )
    assert (
        settings.database_url == "postgresql+asyncpg://user:pass@db:5432/app"
    )


def test_settings_rejects_excessive_app_client_demand(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(RuntimeError, match="Connection budget exceeded"):
        _load_settings(
            monkeypatch,
            APP_INSTANCE_COUNT="3",
            DB_POOL_SIZE="10",
            DB_MAX_OVERFLOW="20",
            PGBOUNCER_MAX_CLIENT_CONN="50",
        )


def test_settings_rejects_invalid_pgbouncer_server_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(RuntimeError, match="Invalid PgBouncer budget"):
        _load_settings(
            monkeypatch,
            PGBOUNCER_DEFAULT_POOL_SIZE="80",
            PGBOUNCER_RESERVE_POOL_SIZE="30",
            PGBOUNCER_MAX_DB_CONNECTIONS="100",
        )


def test_settings_rejects_pgbouncer_budget_over_postgres_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(
        RuntimeError,
        match="PgBouncer DB budget exceeds Postgres capacity",
    ):
        _load_settings(
            monkeypatch,
            PGBOUNCER_MAX_DB_CONNECTIONS="100",
            POSTGRES_MAX_CONNECTIONS="80",
            POSTGRES_SUPERUSER_RESERVED_CONNECTIONS="3",
        )
