from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.application.common.interfaces.ports.persistence.manager import (
    SessionProtocol,
)


def create_engine(
    url: str,
    *,
    echo: bool = False,
    pool_size: int = 10,
    max_overflow: int = 20,
    pool_timeout_s: int = 30,
    pool_recycle_s: int = 1800,
    connect_timeout_s: int = 10,
) -> AsyncEngine:
    engine_kwargs: dict[str, object] = {
        "echo": echo,
        "pool_pre_ping": True,
        "connect_args": {"timeout": connect_timeout_s},
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_timeout": pool_timeout_s,
        "pool_recycle": pool_recycle_s,
    }
    return create_async_engine(
        url,
        **engine_kwargs,
    )


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def require_async_session(session: SessionProtocol) -> AsyncSession:
    if isinstance(session, AsyncSession):
        return session
    raise TypeError("SessionProtocol must be AsyncSession")


async def session_dependency(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
