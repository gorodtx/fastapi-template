import re
from typing import ClassVar
from dataclasses import dataclass


from src.domain.core.exceptions.user_exceptions import InvalidEmailFormatError
from src.domain.core.value_objects.base import SingleValueObject



@dataclass(frozen=True, eq=True)
class Email(SingleValueObject[str]):

    EMAIL_REGEX: ClassVar[re.Pattern] = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    MAX_LENGTH: ClassVar[int] = 254

    def _validate(self) -> None:
        if not self.value:
            raise InvalidEmailFormatError("Email не может быть пустым", )

        if len(self.value) > self.MAX_LENGTH:
            raise InvalidEmailFormatError(f"Email слишком длинный (максимум {self.MAX_LENGTH} символов)")

        if not self.EMAIL_REGEX.match(self.value):
            raise InvalidEmailFormatError(f"Неверный формат email: {self.value}")

        object.__setattr__(self, 'value', self.value.lower())

    @classmethod
    def create(cls, email_str: str) -> 'Email':
        return cls(email_str.strip().lower())
