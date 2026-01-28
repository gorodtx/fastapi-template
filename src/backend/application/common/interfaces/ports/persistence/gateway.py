from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.application.common.interfaces.ports.persistence.manager import (
    TransactionManager,
)
from backend.application.common.interfaces.ports.persistence.rbac_adapter import (
    RbacAdapter,
)
from backend.application.common.interfaces.ports.persistence.users_adapter import (
    UsersAdapter,
)


@runtime_checkable
class PersistenceGateway(Protocol):
    manager: TransactionManager
    users: UsersAdapter
    rbac: RbacAdapter
