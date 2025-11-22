from __future__ import annotations


class ConstraintViolationError(Exception):
    def __init__(
        self,
        constraint: str,
        message: str | None = None,
        field: str | None = None,
    ) -> None:
        super().__init__(f"Constraint violated: {constraint}")
        self.constraint = constraint
        self.message = message
        self.field = field
