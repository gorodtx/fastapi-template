from __future__ import annotations

from backend.application.common.interfaces.ports.cache import StrCache
from backend.application.common.interfaces.ports.persistence import (
    PersistenceGateway,
    Query,
    RbacAdapter,
    SessionProtocol,
    TransactionManager,
    TransactionScope,
    UsersAdapter,
)
from backend.application.common.interfaces.ports.serialization import (
    DTO,
    Deserializable,
    DTOCodec,
    Serializable,
)
from backend.application.common.interfaces.ports.shared_lock import SharedLock

__all__: list[str] = [
    "DTO",
    "DTOCodec",
    "Deserializable",
    "PersistenceGateway",
    "Query",
    "RbacAdapter",
    "Serializable",
    "SessionProtocol",
    "SharedLock",
    "StrCache",
    "TransactionManager",
    "TransactionScope",
    "UsersAdapter",
]
