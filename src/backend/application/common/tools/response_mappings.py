from __future__ import annotations

from backend.application.common.dtos.users import (
    UserResponseDTO,
    UserWithRolesDTO,
)
from backend.application.common.tools.response_mapper import ResponseMapper
from backend.domain.core.entities.user import User


def _user_to_response_dto(user: User) -> UserResponseDTO:
    return UserResponseDTO(
        id=user.id,
        email=user.email.value,
        login=user.login.value,
        username=user.username.value,
    )


def _user_to_with_roles_dto(user: User) -> UserWithRolesDTO:
    roles = [role.value for role in user.roles]
    return UserWithRolesDTO(
        id=user.id,
        email=user.email.value,
        login=user.login.value,
        username=user.username.value,
        roles=roles,
        permissions=[],
    )


def build_response_mapper() -> ResponseMapper:
    mapper = ResponseMapper()
    mapper.register(User, UserResponseDTO, _user_to_response_dto)
    mapper.register(User, UserWithRolesDTO, _user_to_with_roles_dto)
    return mapper


DEFAULT_RESPONSE_MAPPER: ResponseMapper = build_response_mapper()
