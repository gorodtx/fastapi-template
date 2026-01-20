from __future__ import annotations

from backend.application.common.exceptions.application import AppError, ConflictError
from backend.domain.core.exceptions.base import DomainError, DomainTypeError


def map_user_input_error(exc: Exception) -> AppError:
    if isinstance(exc, (ValueError, DomainTypeError, DomainError, RuntimeError)):
        return ConflictError(f"Invalid input: {exc}")
    raise exc
