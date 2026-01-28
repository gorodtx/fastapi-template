from __future__ import annotations

from collections.abc import Callable

from backend.application.common.exceptions.application import (
    AppError,
    ConflictError,
)
from backend.domain.core.exceptions.rbac import RoleNotAssignedError


def map_role_input_error(
    raw_role: str, *, allow_unassigned: bool = False
) -> Callable[[Exception], AppError]:
    def mapper(exc: Exception) -> AppError:
        if isinstance(exc, ValueError):
            return ConflictError(f"Unknown role {raw_role!r}")
        if allow_unassigned and isinstance(exc, RoleNotAssignedError):
            return ConflictError(str(exc))
        raise exc

    return mapper
