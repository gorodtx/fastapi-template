from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict

from backend.application.common.dtos.base import DTO


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    @classmethod
    def from_dto(cls: type[Self], dto: DTO) -> Self:
        return cls.model_validate(dto, from_attributes=True)
