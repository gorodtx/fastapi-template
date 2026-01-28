from __future__ import annotations

from backend.domain.core.value_objects.access.permission_code import (
    PermissionCode,
)
from backend.domain.core.value_objects.base import ValueObject, value_object
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.domain.core.value_objects.password import Password

__all__: list[str] = [
    "Email",
    "Login",
    "Password",
    "PermissionCode",
    "Username",
    "ValueObject",
    "value_object",
]
