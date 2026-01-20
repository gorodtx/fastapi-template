from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from backend.application.common.interfaces.infra.persistence.gateway import PersistenceGateway
from backend.application.common.interfaces.infra.persistence.manager import TransactionManager
from backend.domain.ports.security.password_hasher import PasswordHasherPort
from backend.infrastructure.persistence.manager import TransactionManagerImpl
from backend.infrastructure.persistence.persistence_gateway import PersistenceGatewayImpl
from backend.infrastructure.persistence.sqlalchemy.session_db import (
    create_engine,
    create_session_factory,
)
from backend.infrastructure.security.password_hasher import Argon2PasswordHasher
from dishka import Provider, Scope, provide


class PersistenceProvider(Provider):
    @provide(scope=Scope.APP)
    def engine(self) -> AsyncEngine:
        return create_engine()

    @provide(scope=Scope.APP)
    def session_factory(
        self,
        engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        return create_session_factory(engine)

    @provide(scope=Scope.REQUEST)
    async def session(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def transaction_manager(self, session: AsyncSession) -> TransactionManager:
        return TransactionManagerImpl(session)

    @provide(scope=Scope.REQUEST)
    def persistence_gateway(self, manager: TransactionManager) -> PersistenceGateway:
        return PersistenceGatewayImpl(manager)

    @provide(scope=Scope.APP)
    def password_hasher(self) -> PasswordHasherPort:
        return Argon2PasswordHasher()
