from __future__ import annotations

from pydantic.functional_validators import field_validator
from pydantic.main import BaseModel

from backend.application.common.tools.password_validator import (
    RawPasswordValidator,
)


class BaseShema(BaseModel):
    @field_validator("raw_password", check_fields=False)
    @classmethod
    def _validate_password(cls: type[BaseShema], value: str) -> str:
        RawPasswordValidator.validate(value)
        return value
