from __future__ import annotations


class DomainError(Exception):
    """Base domain business rule violation error."""

    ...


class DomainTypeError(DomainError):
    """Error in domain type (Value Object) construction."""

    ...


class CorruptedInvariantError(DomainError):
    """
    Critical system invariant violation.

    Exception for situations that should NEVER happen,
    but if they do - it will be catastrophic (double money charge,
    critical data corruption, etc.)

    Requires immediate logging and monitoring.
    """

    ...


class ItemNotFoundError(DomainError):
    """Requested entity not found."""

    ...


class ForbiddenOperationError(DomainError):
    """Operation forbidden for current object state or user."""

    ...
