from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator

from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.infrastructure.persistence.sqlalchemy.types.base import (
    bind_vo,
    result_vo,
)


class EmailType(TypeDecorator[Email]):
    impl: String = String(255)
    cache_ok: bool = True

    def process_bind_param(
        self: EmailType, value: Email | None, dialect: Dialect
    ) -> str | None:
        del dialect
        return bind_vo(value, Email)

    def process_result_value(
        self: EmailType, value: str | None, dialect: Dialect
    ) -> Email | None:
        del dialect
        return result_vo(value, Email)


class LoginType(TypeDecorator[Login]):
    impl: String = String(20)
    cache_ok: bool = True

    def process_bind_param(
        self: LoginType, value: Login | None, dialect: Dialect
    ) -> str | None:
        del dialect
        return bind_vo(value, Login)

    def process_result_value(
        self: LoginType, value: str | None, dialect: Dialect
    ) -> Login | None:
        del dialect
        return result_vo(value, Login)


class UsernameType(TypeDecorator[Username]):
    impl: String = String(20)
    cache_ok: bool = True

    def process_bind_param(
        self: UsernameType, value: Username | None, dialect: Dialect
    ) -> str | None:
        del dialect
        return bind_vo(value, Username)

    def process_result_value(
        self: UsernameType, value: str | None, dialect: Dialect
    ) -> Username | None:
        del dialect
        return result_vo(value, Username)
