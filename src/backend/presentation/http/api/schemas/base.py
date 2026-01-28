from __future__ import annotations

from typing import Self

from pydantic.functional_validators import field_validator
from pydantic.main import BaseModel

from backend.application.common.dtos.base import DTO
from backend.application.common.tools.password_validator import (
    RawPasswordValidator,
)


class BaseShema(BaseModel):
    @classmethod
    def from_dto(cls: type[Self], dto: DTO) -> Self:
        return cls.model_validate(dto, from_attributes=True)

    @field_validator("raw_password", check_fields=False)
    @classmethod
    def _validate_password(cls: type[BaseShema], value: str) -> str:
        RawPasswordValidator.validate(raw_password=value)
        return value
