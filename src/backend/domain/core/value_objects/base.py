from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Type, TypeVar, Sequence, Union, overload, dataclass_transform
from abc import ABC


V = TypeVar("V", bound="ValueObject")
Validator = Callable[[V], None]


@dataclass_transform(
    frozen_default=True, eq_default=True, kw_only_default=False, field_specifiers=()
)
@overload
def value_object(cls: Type[V]) -> Type[V]: ...
@overload
def value_object(
    *, validate: Union[Validator, Sequence[Validator]]
) -> Callable[[Type[V]], Type[V]]: ...


def value_object(
    cls: type[V] | None = None, *, validate: Union[Validator, Sequence[Validator]] | None = None
) -> type[V] | Callable[[type[V]], type[V]]:
    def decorator(cls_inner: type[V]) -> type[V]:
        dc = dataclass(frozen=True, eq=True)(cls_inner)
        if validate:
            validators = validate if isinstance(validate, Sequence) else (validate,)
            orig = getattr(dc, "__post_init__", None)

            def __post_init__(self: V) -> None:
                if orig:
                    orig(self)
                for fn in validators:
                    fn(self)

            setattr(dc, "__post_init__", __post_init__)
        return dc

    return decorator if cls is None else decorator(cls)


class ValueObject(ABC):
    def __str__(self) -> str:
        fields = self.__dict__
        if list(fields.keys()) == ["value"]:
            return str(fields["value"])
        return f"{self.__class__.__name__}({fields})"

    def __repr__(self) -> str:
        return self.__str__()
