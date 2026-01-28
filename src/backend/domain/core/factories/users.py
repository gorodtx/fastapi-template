from __future__ import annotations

from dataclasses import dataclass

from uuid_utils.compat import UUID

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.user import User
from backend.domain.core.exceptions.base import DomainTypeError
from backend.domain.core.exceptions.user import UserDataCorruptedError
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.domain.core.value_objects.password import Password


def _type_error(field: str, exc: Exception) -> DomainTypeError:
    return DomainTypeError(f"{field}: {exc}")


def _corrupted_error(
    user_id: UUID, field: str, exc: Exception
) -> UserDataCorruptedError:
    return UserDataCorruptedError(user_id=user_id, details=f"{field}: {exc}")


@dataclass(frozen=True, slots=True)
class UserFactory:
    @staticmethod
    def email(value: str) -> Email:
        try:
            return Email(value)
        except (TypeError, ValueError) as exc:
            raise _type_error("email", exc) from exc

    @staticmethod
    def login(value: str) -> Login:
        try:
            return Login(value)
        except (TypeError, ValueError) as exc:
            raise _type_error("login", exc) from exc

    @staticmethod
    def username(value: str) -> Username:
        try:
            return Username(value)
        except (TypeError, ValueError) as exc:
            raise _type_error("username", exc) from exc

    @staticmethod
    def password_from_hash(value: str) -> Password:
        try:
            return Password(value)
        except (TypeError, ValueError) as exc:
            raise _type_error("password_hash", exc) from exc

    @staticmethod
    def register(
        *,
        id: UUID,
        email: str,
        login: str,
        username: str,
        password_hash: str,
    ) -> User:
        email_vo = UserFactory.email(email)
        login_vo = UserFactory.login(login)
        username_vo = UserFactory.username(username)
        password_vo = UserFactory.password_from_hash(password_hash)
        return User.register(
            id=id,
            email=email_vo,
            login=login_vo,
            username=username_vo,
            password=password_vo,
        )

    @staticmethod
    def rehydrate(
        *,
        id: UUID,
        email: str,
        login: str,
        username: str,
        password_hash: str,
        is_active: bool,
        roles: set[SystemRole],
    ) -> User:
        try:
            email_vo = Email(email)
        except (TypeError, ValueError) as exc:
            raise _corrupted_error(id, "email", exc) from exc
        try:
            login_vo = Login(login)
        except (TypeError, ValueError) as exc:
            raise _corrupted_error(id, "login", exc) from exc
        try:
            username_vo = Username(username)
        except (TypeError, ValueError) as exc:
            raise _corrupted_error(id, "username", exc) from exc
        try:
            password_vo = Password(password_hash)
        except (TypeError, ValueError) as exc:
            raise _corrupted_error(id, "password_hash", exc) from exc

        return User(
            id=id,
            email=email_vo,
            login=login_vo,
            username=username_vo,
            password=password_vo,
            is_active=is_active,
            roles=roles,
        )

    @staticmethod
    def patch(
        user: User,
        *,
        email: str | None = None,
        login: str | None = None,
        username: str | None = None,
        password_hash: str | None = None,
    ) -> None:
        if email is not None:
            user.change_email(UserFactory.email(email))
        if login is not None:
            user.change_login(UserFactory.login(login))
        if username is not None:
            user.change_username(UserFactory.username(username))
        if password_hash is not None:
            user.change_password(UserFactory.password_from_hash(password_hash))
