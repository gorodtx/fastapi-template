from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator

from backend.domain.core.value_objects.password import Password
from backend.infrastructure.persistence.sqlalchemy.types.base import (
    bind_vo,
    result_vo,
)


class PasswordHashType(TypeDecorator[Password]):
    impl: String = String(255)
    cache_ok: bool = True

    def process_bind_param(
        self: PasswordHashType, value: Password | None, dialect: Dialect
    ) -> str | None:
        del dialect
        return bind_vo(value, Password)

    def process_result_value(
        self: PasswordHashType, value: str | None, dialect: Dialect
    ) -> Password | None:
        del dialect
        return result_vo(value, Password)
