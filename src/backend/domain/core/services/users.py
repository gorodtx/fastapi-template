from __future__ import annotations

from collections.abc import Callable

from uuid_utils.compat import UUID

from backend.domain.core.entities.user import User
from backend.domain.core.exceptions.base import DomainTypeError
from backend.domain.core.exceptions.rbac import RoleNotAssignedError
from backend.domain.core.exceptions.user import UserDataCorruptedError
from backend.domain.core.policies.identity import (
    validate_email,
    validate_login,
    validate_password_hash,
    validate_username,
)
from backend.domain.core.policies.rbac import validate_role_code
from backend.domain.core.types.rbac import RoleCode

_EMAIL_FIELD = "email"
_LOGIN_FIELD = "login"
_USERNAME_FIELD = "username"
_HASH_FIELD = "password_hash"
_ROLES_FIELD = "roles"
_USER_FIELD_VALIDATORS: dict[str, Callable[[str], str]] = {
    _EMAIL_FIELD: validate_email,
    _LOGIN_FIELD: validate_login,
    _USERNAME_FIELD: validate_username,
    _HASH_FIELD: validate_password_hash,
}


def _type_error(field: str, exc: Exception) -> DomainTypeError:
    return DomainTypeError(f"{field}: {exc}")


def _corrupted_error(
    user_id: UUID, field: str, exc: Exception
) -> UserDataCorruptedError:
    return UserDataCorruptedError(user_id=user_id, details=f"{field}: {exc}")


def _coerce_input(
    *, field: str, value: str, validator: Callable[[str], str]
) -> str:
    try:
        return validator(value)
    except (TypeError, ValueError) as exc:
        raise _type_error(field, exc) from exc


def _coerce_corrupted(
    *,
    user_id: UUID,
    field: str,
    value: str,
    validator: Callable[[str], str],
) -> str:
    try:
        return validator(value)
    except (TypeError, ValueError) as exc:
        raise _corrupted_error(user_id, field, exc) from exc


def _validate_role(role: str) -> str:
    return validate_role_code(role)


def build_user(
    *,
    id: UUID,
    email: str,
    login: str,
    username: str,
    password_hash: str,
    is_active: bool = True,
    roles: set[RoleCode] | None = None,
) -> User:
    values: dict[str, str] = {
        _EMAIL_FIELD: email,
        _LOGIN_FIELD: login,
        _USERNAME_FIELD: username,
        _HASH_FIELD: password_hash,
    }
    validated: dict[str, str] = {}
    for field, value in values.items():
        validated[field] = _coerce_input(
            field=field,
            value=value,
            validator=_USER_FIELD_VALIDATORS[field],
        )
    return User(
        id=id,
        email=validated[_EMAIL_FIELD],
        login=validated[_LOGIN_FIELD],
        username=validated[_USERNAME_FIELD],
        password=validated[_HASH_FIELD],
        is_active=is_active,
        roles=set(roles) if roles is not None else set(),
    )


def rehydrate_user(
    *,
    id: UUID,
    email: str,
    login: str,
    username: str,
    password_hash: str,
    is_active: bool,
    roles: set[RoleCode],
) -> User:
    checked_email = _coerce_corrupted(
        user_id=id,
        field=_EMAIL_FIELD,
        value=email,
        validator=validate_email,
    )
    checked_login = _coerce_corrupted(
        user_id=id,
        field=_LOGIN_FIELD,
        value=login,
        validator=validate_login,
    )
    checked_username = _coerce_corrupted(
        user_id=id,
        field=_USERNAME_FIELD,
        value=username,
        validator=validate_username,
    )
    checked_password = _coerce_corrupted(
        user_id=id,
        field=_HASH_FIELD,
        value=password_hash,
        validator=validate_password_hash,
    )
    checked_roles: set[RoleCode] = set()
    for role in roles:
        checked_roles.add(
            _coerce_corrupted(
                user_id=id,
                field=_ROLES_FIELD,
                value=role,
                validator=_validate_role,
            )
        )
    return User(
        id=id,
        email=checked_email,
        login=checked_login,
        username=checked_username,
        password=checked_password,
        is_active=is_active,
        roles=checked_roles,
    )


def apply_user_patch(
    user: User,
    *,
    email: str | None = None,
    login: str | None = None,
    username: str | None = None,
    password_hash: str | None = None,
) -> None:
    updates: dict[str, str] = {}
    if email is not None:
        updates[_EMAIL_FIELD] = email
    if login is not None:
        updates[_LOGIN_FIELD] = login
    if username is not None:
        updates[_USERNAME_FIELD] = username
    if password_hash is not None:
        updates[_HASH_FIELD] = password_hash
    for field, raw_value in updates.items():
        checked_value = _coerce_input(
            field=field,
            value=raw_value,
            validator=_USER_FIELD_VALIDATORS[field],
        )
        if field == _EMAIL_FIELD:
            user.email = checked_value
        elif field == _LOGIN_FIELD:
            user.login = checked_value
        elif field == _USERNAME_FIELD:
            user.username = checked_value
        else:
            user.password = checked_value


def revoke_user_role(user: User, role: RoleCode) -> None:
    if role not in user.roles:
        raise RoleNotAssignedError(role=role, user_id=user.id)
    user.roles.remove(role)
