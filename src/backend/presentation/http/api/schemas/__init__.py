from __future__ import annotations

from backend.presentation.http.api.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SuccessResponse,
    TokenPairResponse,
)
from backend.presentation.http.api.schemas.base import BaseShema
from backend.presentation.http.api.schemas.rbac import (
    RoleChangeRequest,
    UserRolesResponse,
)
from backend.presentation.http.api.schemas.users import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)

__all__: list[str] = [
    "BaseShema",
    "LoginRequest",
    "LogoutRequest",
    "RefreshRequest",
    "RoleChangeRequest",
    "SuccessResponse",
    "TokenPairResponse",
    "UserCreateRequest",
    "UserResponse",
    "UserRolesResponse",
    "UserUpdateRequest",
]
