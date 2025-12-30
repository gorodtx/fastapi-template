from __future__ import annotations

from backend.application.common.exceptions.application import ConflictError
from backend.application.common.exceptions.db import ConstraintViolationError


def map_infra_error_to_application(error: ConstraintViolationError) -> ConflictError:
    message = error.message
    if message is None:
        message = f"Constraint violated: {error.constraint}"
    return ConflictError(message)
