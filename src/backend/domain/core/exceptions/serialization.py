from __future__ import annotations

from backend.domain.core.exceptions.base import DomainTypeError


class DomainSerializationError(DomainTypeError):
    """Error raised when a domain value cannot be serialized or deserialized."""
