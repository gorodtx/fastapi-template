from __future__ import annotations

from dataclasses import dataclass
from typing import Any, dataclass_transform #декоратор для превращения класса в датакласс


import uuid_utils.compat as uuid
from msgspec import to_builtins


TypeID = uuid.UUID



@dataclass_transform()
def entity[E](cls: type[E]) -> type[E]:
    return dataclass()(cls)



@entity
class Entity:
    id: TypeID
    
    def asdict(self) -> dict[str, Any]:
        return to_builtins(self, str_keys=True)
    