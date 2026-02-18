from __future__ import annotations

from backend.application.common.dtos.users import UserResponseDTO
from backend.domain.core.entities.user import User


def present_user_response(user: User) -> UserResponseDTO:
    return UserResponseDTO(
        id=user.id,
        email=user.email,
        login=user.login,
        username=user.username,
    )
