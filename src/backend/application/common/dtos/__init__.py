from __future__ import annotations

from backend.application.common.dtos.auth import (
    LoginUserDTO,
    LogoutUserDTO,
    RefreshUserDTO,
    SuccessDTO,
    TokenPairDTO,
)
from backend.application.common.dtos.base import DTO, dto
from backend.application.common.dtos.rbac import (
    AssignRoleToUserDTO,
    GetUserRolesDTO,
    GetUsersByRoleDTO,
    RevokeRoleFromUserDTO,
    RoleAssignmentResultDTO,
    UserRolesResponseDTO,
    UsersByRoleResponseDTO,
)
from backend.application.common.dtos.users import (
    DeleteUserDTO,
    GetUserDTO,
    GetUserWithRolesDTO,
    UserCreateDTO,
    UserResponseDTO,
    UserUpdateDTO,
    UserWithRolesDTO,
)

__all__: list[str] = [
    "DTO",
    "AssignRoleToUserDTO",
    "DeleteUserDTO",
    "GetUserDTO",
    "GetUserRolesDTO",
    "GetUserWithRolesDTO",
    "GetUsersByRoleDTO",
    "LoginUserDTO",
    "LogoutUserDTO",
    "RefreshUserDTO",
    "RevokeRoleFromUserDTO",
    "RoleAssignmentResultDTO",
    "SuccessDTO",
    "TokenPairDTO",
    "UserCreateDTO",
    "UserResponseDTO",
    "UserRolesResponseDTO",
    "UserUpdateDTO",
    "UserWithRolesDTO",
    "UsersByRoleResponseDTO",
    "dto",
]
