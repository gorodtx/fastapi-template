from __future__ import annotations

from collections.abc import Callable
from typing import overload

from uuid_utils.compat import UUID

from backend.domain.core.constants.rbac import SystemRole
from backend.domain.core.entities.user import User
from backend.domain.core.exceptions.base import DomainTypeError
from backend.domain.core.exceptions.user import UserDataCorruptedError
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.domain.core.value_objects.password import Password


def _input_error(field: str, exc: Exception) -> DomainTypeError:
    return DomainTypeError(f"{field}: {exc}")


def _storage_error(user_id: UUID) -> Callable[[str, Exception], UserDataCorruptedError]:
    def _mapper(field: str, exc: Exception) -> UserDataCorruptedError:
        return UserDataCorruptedError(user_id=user_id, details=f"{field}: {exc}")

    return _mapper


@overload
def _build_vo(
    *,
    field: str,
    raw: str,
    ctor: type[Email],
    map_error: Callable[[str, Exception], Exception],
) -> Email: ...


@overload
def _build_vo(
    *,
    field: str,
    raw: str,
    ctor: type[Login],
    map_error: Callable[[str, Exception], Exception],
) -> Login: ...


@overload
def _build_vo(
    *,
    field: str,
    raw: str,
    ctor: type[Username],
    map_error: Callable[[str, Exception], Exception],
) -> Username: ...


@overload
def _build_vo(
    *,
    field: str,
    raw: str,
    ctor: type[Password],
    map_error: Callable[[str, Exception], Exception],
) -> Password: ...


def _build_vo(
    *,
    field: str,
    raw: str,
    ctor: Callable[[str], Email | Login | Username | Password],
    map_error: Callable[[str, Exception], Exception],
) -> Email | Login | Username | Password:
    try:
        return ctor(raw)
    except (TypeError, ValueError) as exc:
        raise map_error(field, exc) from exc


class UserFactory:
    __slots__ = ()

    @staticmethod
    def register(
        *,
        id: UUID,
        email: str,
        login: str,
        username: str,
        password_hash: str,
    ) -> User:
        return User.register(
            id=id,
            email=_build_vo(field="email", raw=email, ctor=Email, map_error=_input_error),
            login=_build_vo(field="login", raw=login, ctor=Login, map_error=_input_error),
            username=_build_vo(
                field="username", raw=username, ctor=Username, map_error=_input_error
            ),
            password=_build_vo(
                field="password_hash",
                raw=password_hash,
                ctor=Password,
                map_error=_input_error,
            ),
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
        map_err = _storage_error(id)
        return User.rehydrate(
            id=id,
            email=_build_vo(field="email", raw=email, ctor=Email, map_error=map_err),
            login=_build_vo(field="login", raw=login, ctor=Login, map_error=map_err),
            username=_build_vo(field="username", raw=username, ctor=Username, map_error=map_err),
            password=_build_vo(
                field="password_hash",
                raw=password_hash,
                ctor=Password,
                map_error=map_err,
            ),
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
            user.change_email(
                _build_vo(field="email", raw=email, ctor=Email, map_error=_input_error)
            )
        if login is not None:
            user.change_login(
                _build_vo(field="login", raw=login, ctor=Login, map_error=_input_error)
            )
        if username is not None:
            user.change_username(
                _build_vo(field="username", raw=username, ctor=Username, map_error=_input_error)
            )
        if password_hash is not None:
            user.change_password(
                _build_vo(
                    field="password_hash",
                    raw=password_hash,
                    ctor=Password,
                    map_error=_input_error,
                )
            )


__all__ = ["UserFactory"]
