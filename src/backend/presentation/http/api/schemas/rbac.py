from __future__ import annotations

from typing import Annotated, Final

from pydantic import StringConstraints, field_validator
from uuid_utils.compat import UUID

from backend.domain.core.value_objects.access.role_code import RoleCode
from backend.presentation.http.api.schemas.base import BaseShema

_MIN_ROLE_CODE_LENGTH: Final[int] = 3
_MAX_ROLE_CODE_LENGTH: Final[int] = 64
_ROLE_CODE_PATTERN: Final[str] = r"^[a-z][a-z0-9_]{2,63}$"

type RoleCodeStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=_MIN_ROLE_CODE_LENGTH,
        max_length=_MAX_ROLE_CODE_LENGTH,
        pattern=_ROLE_CODE_PATTERN,
    ),
]


class UserRolesResponse(BaseShema):
    user_id: UUID
    roles: list[str]
    permissions: list[str]


class RoleChangeRequest(BaseShema):
    role_code: RoleCodeStr

    @field_validator("role_code")
    @classmethod
    def _validate_role_code(cls: type[RoleChangeRequest], value: str) -> str:
        RoleCode(value)
        return value
