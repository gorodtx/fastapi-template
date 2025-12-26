from __future__ import annotations

from backend.application.common.dtos.users import UserResponseDTO
from backend.domain.core.entities.user import User


class UserMapper:
    __slots__ = ()

    @staticmethod
    def to_dto(entity: User) -> UserResponseDTO:
        return UserResponseDTO(
            id=entity.id,
            email=entity.email.value,
            login=entity.login.value,
            username=entity.username.value,
        )

    @staticmethod
    def to_many_dto(entities: list[User]) -> list[UserResponseDTO]:
        return [UserMapper.to_dto(entity) for entity in entities]
