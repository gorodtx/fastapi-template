from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator

from backend.domain.core.value_objects.password import Password
from backend.infrastructure.persistence.sqlalchemy.types.base import bind_vo, result_vo


class PasswordHashType(TypeDecorator[Password]):
    impl = String(255)
    cache_ok = True

    def process_bind_param(self, value: Password | None, dialect: Dialect) -> str | None:
        del dialect
        return bind_vo(value, Password)

    def process_result_value(self, value: str | None, dialect: Dialect) -> Password | None:
        del dialect
        return result_vo(value, Password)
