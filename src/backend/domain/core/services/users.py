from __future__ import annotations

from uuid_utils.compat import UUID

from backend.domain.core.entities.user import User
from backend.domain.core.exceptions.rbac import RoleNotAssignedError
from backend.domain.core.exceptions.user import UserDataCorruptedError
from backend.domain.core.types.rbac import RoleCode


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
        email=email,
        login=login,
        username=username,
        password=password_hash,
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
    for role in roles:
        if not isinstance(role, str):
            raise UserDataCorruptedError(
                user_id=id, details="roles: invalid role entry"
            )
    return User(
        id=id,
        email=email,
        login=login,
        username=username,
        password=password_hash,
        is_active=is_active,
        roles=set(roles),
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
        user.email = email
    if login is not None:
        user.login = login
    if username is not None:
        user.username = username
    if password_hash is not None:
        user.password = password_hash


def revoke_user_role(user: User, role: RoleCode) -> None:
    if role not in user.roles:
        raise RoleNotAssignedError(role=role, user_id=user.id)
    user.roles.remove(role)
