from __future__ import annotations

from dataclasses import dataclass
from typing import dataclass_transform

import uuid_utils.compat as uuid

TypeID = uuid.UUID


@dataclass_transform(kw_only_default=True)
def entity[E](cls: type[E]) -> type[E]:
    return dataclass(kw_only=True)(cls)


@entity
class Entity:
    id: TypeID
