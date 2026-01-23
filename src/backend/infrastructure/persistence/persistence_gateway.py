from __future__ import annotations

from backend.application.common.interfaces.ports.persistence.gateway import PersistenceGateway
from backend.application.common.interfaces.ports.persistence.manager import TransactionManager
from backend.infrastructure.persistence.adapters.rbac import SqlRbacAdapter
from backend.infrastructure.persistence.adapters.users import SqlUsersAdapter


class PersistenceGatewayImpl(PersistenceGateway):
    def __init__(self, manager: TransactionManager) -> None:
        self.manager = manager
        self.users = SqlUsersAdapter(manager)
        self.rbac = SqlRbacAdapter(manager)
