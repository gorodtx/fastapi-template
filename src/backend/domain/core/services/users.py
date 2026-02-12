from __future__ import annotations

from uuid_utils.compat import UUID

from backend.domain.core.entities.user import User
from backend.domain.core.exceptions.base import DomainTypeError
from backend.domain.core.exceptions.rbac import RoleNotAssignedError
from backend.domain.core.exceptions.user import UserDataCorruptedError
from backend.domain.core.policies.identity import (
    normalize_email,
    normalize_login,
    normalize_password_hash,
    normalize_username,
    validate_email,
    validate_login,
    validate_password_hash,
    validate_username,
)
from backend.domain.core.policies.rbac import (
    normalize_role_code,
    validate_role_code,
)
from backend.domain.core.types.rbac import RoleCode


def _type_error(field: str, exc: Exception) -> DomainTypeError:
    return DomainTypeError(f"{field}: {exc}")


def _corrupted_error(
    user_id: UUID, field: str, exc: Exception
) -> UserDataCorruptedError:
    return UserDataCorruptedError(user_id=user_id, details=f"{field}: {exc}")


def validate_and_normalize_email(value: str) -> str:
    try:
        return validate_email(normalize_email(value))
    except (TypeError, ValueError) as exc:
        raise _type_error("email", exc) from exc


def validate_and_normalize_login(value: str) -> str:
    try:
        return validate_login(normalize_login(value))
    except (TypeError, ValueError) as exc:
        raise _type_error("login", exc) from exc


def validate_and_normalize_username(value: str) -> str:
    try:
        return validate_username(normalize_username(value))
    except (TypeError, ValueError) as exc:
        raise _type_error("username", exc) from exc


def validate_and_normalize_password_hash(value: str) -> str:
    try:
        return validate_password_hash(normalize_password_hash(value))
    except (TypeError, ValueError) as exc:
        raise _type_error("password_hash", exc) from exc


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
    return User(
        id=id,
        email=validate_and_normalize_email(email),
        login=validate_and_normalize_login(login),
        username=validate_and_normalize_username(username),
        password=validate_and_normalize_password_hash(password_hash),
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
    try:
        checked_email = validate_email(normalize_email(email))
    except (TypeError, ValueError) as exc:
        raise _corrupted_error(id, "email", exc) from exc
    try:
        checked_login = validate_login(normalize_login(login))
    except (TypeError, ValueError) as exc:
        raise _corrupted_error(id, "login", exc) from exc
    try:
        checked_username = validate_username(normalize_username(username))
    except (TypeError, ValueError) as exc:
        raise _corrupted_error(id, "username", exc) from exc
    try:
        checked_password = validate_password_hash(
            normalize_password_hash(password_hash)
        )
    except (TypeError, ValueError) as exc:
        raise _corrupted_error(id, "password_hash", exc) from exc
    checked_roles: set[RoleCode] = set()
    try:
        for role in roles:
            checked_roles.add(validate_role_code(normalize_role_code(role)))
    except (TypeError, ValueError) as exc:
        raise _corrupted_error(id, "roles", exc) from exc
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
    if email is not None:
        user.email = validate_and_normalize_email(email)
    if login is not None:
        user.login = validate_and_normalize_login(login)
    if username is not None:
        user.username = validate_and_normalize_username(username)
    if password_hash is not None:
        user.password = validate_and_normalize_password_hash(password_hash)


def assign_user_role(user: User, role: RoleCode) -> None:
    user.roles.add(role)


def revoke_user_role(user: User, role: RoleCode) -> None:
    if role not in user.roles:
        raise RoleNotAssignedError(role=role, user_id=user.id)
    user.roles.remove(role)
