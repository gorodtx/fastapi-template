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
) -> AsyncEngine:
    return create_async_engine(
        url,
        echo=echo,
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
