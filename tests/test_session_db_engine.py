from __future__ import annotations

import pytest

from backend.infrastructure.persistence.sqlalchemy import session_db


def test_create_engine_applies_pool_and_timeout_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    engine = object()

    def _create_async_engine(url: str, **kwargs: object) -> object:
        captured["url"] = url
        captured.update(kwargs)
        return engine

    monkeypatch.setattr(
        session_db, "create_async_engine", _create_async_engine
    )

    created = session_db.create_engine(
        "postgresql+asyncpg://user:pass@db:5432/app",
        echo=True,
        pool_size=11,
        max_overflow=33,
        pool_timeout_s=42,
        pool_recycle_s=1234,
        connect_timeout_s=7,
    )

    assert created is engine
    assert captured["url"] == "postgresql+asyncpg://user:pass@db:5432/app"
    assert captured["echo"] is True
    assert captured["pool_size"] == 11
    assert captured["max_overflow"] == 33
    assert captured["pool_timeout"] == 42
    assert captured["pool_recycle"] == 1234
    assert captured["pool_pre_ping"] is True
    assert captured["connect_args"] == {"timeout": 7}


def test_create_engine_applies_pool_settings_for_pgbouncer_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    engine = object()

    def _create_async_engine(url: str, **kwargs: object) -> object:
        captured["url"] = url
        captured.update(kwargs)
        return engine

    monkeypatch.setattr(
        session_db, "create_async_engine", _create_async_engine
    )

    created = session_db.create_engine(
        "postgresql+asyncpg://user:pass@pgbouncer:5432/app",
        pool_size=11,
        max_overflow=33,
        pool_timeout_s=42,
        pool_recycle_s=1234,
        connect_timeout_s=7,
    )

    assert created is engine
    assert (
        captured["url"] == "postgresql+asyncpg://user:pass@pgbouncer:5432/app"
    )
    assert captured["pool_size"] == 11
    assert captured["max_overflow"] == 33
    assert captured["pool_timeout"] == 42
    assert captured["pool_recycle"] == 1234
    assert captured["pool_pre_ping"] is True
    assert captured["connect_args"] == {"timeout": 7}
