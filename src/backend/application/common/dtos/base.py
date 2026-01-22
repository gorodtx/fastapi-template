from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, dataclass_transform


@dataclass_transform(
    frozen_default=True,
    kw_only_default=True,
)
def dto[T](cls: type[T], /) -> type[T]:
    return dataclass(frozen=True, slots=True, kw_only=True)(cls)


class DTO(Protocol):
    """Marker protocol for DTOs."""
