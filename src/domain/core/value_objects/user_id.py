from dataclasses import dataclass
import uuid_utils as uuid

from src.domain.core.value_objects.base import SingleValueObject



@dataclass(frozen=True, eq=True)
class UserId(SingleValueObject[uuid.UUID]):

    def _validate(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise ValueError("UserId должен быть UUID")

    @classmethod
    def generate(cls) -> 'UserId':
        return cls(uuid.uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> 'UserId':
        return cls(uuid.UUID(id_str))
