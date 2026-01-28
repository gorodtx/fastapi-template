from __future__ import annotations

from backend.application.common.exceptions.application import (
    AppError,
    AuthorizationError,
    ConflictError,
    PermissionDeniedError,
    ResourceNotFoundError,
    RoleHierarchyViolationError,
    UnauthenticatedError,
)
from backend.application.common.exceptions.db import ConstraintViolationError
from backend.application.common.exceptions.storage import (
    NotFoundStorageError,
    StorageError,
)

__all__: list[str] = [
    "AppError",
    "AuthorizationError",
    "ConflictError",
    "ConstraintViolationError",
    "NotFoundStorageError",
    "PermissionDeniedError",
    "ResourceNotFoundError",
    "RoleHierarchyViolationError",
    "StorageError",
    "UnauthenticatedError",
]
