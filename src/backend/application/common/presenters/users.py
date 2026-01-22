from __future__ import annotations

from backend.application.common.dtos.users import UserResponseDTO, UserWithRolesDTO
from backend.application.common.tools.response_mappings import DEFAULT_RESPONSE_MAPPER
from backend.domain.core.entities.user import User


def present_user_response(user: User) -> UserResponseDTO:
    return DEFAULT_RESPONSE_MAPPER.present(user, UserResponseDTO)


def present_user_with_roles(user: User) -> UserWithRolesDTO:
    return DEFAULT_RESPONSE_MAPPER.present(user, UserWithRolesDTO)
