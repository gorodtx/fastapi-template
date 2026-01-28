from __future__ import annotations

from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.interfaces.ports.persistence.manager import (
    Query,
    SessionProtocol,
    TransactionManager,
    TransactionScope,
)
from backend.application.common.interfaces.ports.persistence.rbac_adapter import (
    RbacAdapter,
)
from backend.application.common.interfaces.ports.persistence.users_adapter import (
    UsersAdapter,
)

__all__: list[str] = [
    "PersistenceGateway",
    "Query",
    "RbacAdapter",
    "SessionProtocol",
    "TransactionManager",
    "TransactionScope",
    "UsersAdapter",
]
