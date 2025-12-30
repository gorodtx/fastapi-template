from __future__ import annotations

import importlib
import os
import sys
from logging.config import fileConfig
from pathlib import Path
from typing import Final

from alembic import context
from sqlalchemy import MetaData, engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


_ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]
_SRC_DIR: Final[Path] = _ROOT_DIR / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.append(str(_SRC_DIR))


def _get_target_metadata() -> MetaData:
    module = importlib.import_module("backend.infrastructure.persistence.sqlalchemy.models.base")
    metadata = getattr(module, "metadata", None)
    if not isinstance(metadata, MetaData):
        raise RuntimeError("Failed to load SQLAlchemy metadata for Alembic")
    return metadata


target_metadata = _get_target_metadata()


def _get_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    config_url = config.get_main_option("sqlalchemy.url")
    if config_url:
        return config_url
    raise RuntimeError("DATABASE_URL or sqlalchemy.url must be set for Alembic")


def run_migrations_offline() -> None:
    url = _get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _get_database_url()
    config.set_main_option("sqlalchemy.url", url)

    section = config.get_section(config.config_ini_section, {})
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
