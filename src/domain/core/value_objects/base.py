from __future__ import annotations


from typing import TypeVar, Generic
from abc import ABC, abstractmethod
from dataclasses import dataclass



ValueObjectType = TypeVar('ValueObjectType')


@dataclass(frozen=True, eq=True)
class ValueObject(ABC):
    def __post_init__(self):
        self._validate()

    @abstractmethod
    def _validate(self) -> None:
        pass

    def __str__(self) -> str:
        return str(self.__dict__)


@dataclass(frozen=True, eq=True)
class SingleValueObject(ValueObject, Generic[ValueObjectType]):
    value: ValueObjectType

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"
