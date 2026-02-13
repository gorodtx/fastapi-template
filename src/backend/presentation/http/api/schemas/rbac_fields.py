from __future__ import annotations

from typing import Annotated

from fastapi import Path
from pydantic import AfterValidator, StringConstraints

from backend.domain.core.policies.rbac import (
    MAX_ROLE_CODE_LENGTH,
    MIN_ROLE_CODE_LENGTH,
    ROLE_CODE_PATTERN,
    validate_role_code,
)

type RoleCodeStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=MIN_ROLE_CODE_LENGTH,
        max_length=MAX_ROLE_CODE_LENGTH,
        pattern=ROLE_CODE_PATTERN,
    ),
    AfterValidator(validate_role_code),
]
type RoleCodePath = Annotated[
    str,
    Path(
        min_length=MIN_ROLE_CODE_LENGTH,
        max_length=MAX_ROLE_CODE_LENGTH,
        pattern=ROLE_CODE_PATTERN,
    ),
]
