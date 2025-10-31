from __future__ import annotations

from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.core.value_objects.base import ValueObject, value_object


@value_object()
class UserId(ValueObject):
    value: TypeID
