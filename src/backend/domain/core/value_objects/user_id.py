from __future__ import annotations

import uuid
from backend.domain.core.value_objects.base import value_object, ValueObject


@value_object
class UserId(ValueObject):
    value: uuid.UUID

    @classmethod
    def generate(cls) -> "UserId":  # forward reference
        return cls(value=uuid.uuid4())
