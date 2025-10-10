from typing import Any, Self
from msgspec import Struct, convert, to_builtins


class DTO(Struct, kw_only=True):
    def asdict(self) -> dict[str, Any]:
        return to_builtins(self, str_keys=True)

    @classmethod
    def from_(cls, entity: Any) -> Self:
        return convert(entity, type=cls, from_attributes=True)

    @classmethod
    def from_many(cls, entities: list[Any]) -> list[Self]:
        return [cls.from_(entity) for entity in entities]
