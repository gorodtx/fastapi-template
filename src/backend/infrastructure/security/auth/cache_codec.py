from __future__ import annotations

from collections.abc import Mapping
from typing import TypeGuard

import msgspec
from uuid_utils.compat import UUID

from backend.application.common.interfaces.auth.ports import (
    derive_auth_flags,
)
from backend.application.common.interfaces.auth.types import AuthUser
from backend.domain.core.types.rbac import PermissionCode, RoleCode


def encode_cached_user(user: AuthUser) -> str:
    payload: dict[str, object] = {
        "id": str(user.id),
        "role_codes": list(user.role_codes),
        "permission_codes": [
            permission.value for permission in user.permission_codes
        ],
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_admin": user.is_admin,
        "email": user.email,
    }
    return msgspec.json.encode(payload).decode("utf-8")


def decode_cached_user(raw: str) -> AuthUser | None:
    try:
        raw_data = msgspec.json.decode(raw.encode("utf-8"))
    except msgspec.DecodeError:
        return None
    data = _to_str_key_dict(raw_data)
    if data is None:
        return None
    user_id = data.get("id")
    roles = data.get("role_codes")
    is_active = data.get("is_active")
    email = data.get("email")
    permissions = data.get("permission_codes")
    if (
        not isinstance(user_id, str)
        or not _is_object_list(roles)
        or not _is_object_list(permissions)
        or not isinstance(is_active, bool)
    ):
        return None
    try:
        uid = UUID(user_id)
    except ValueError:
        return None
    role_set: set[RoleCode] = set()
    for raw_role in roles:
        role = _safe_role(raw_role)
        if role is None:
            return None
        role_set.add(role)
    permission_set: set[PermissionCode] = set()
    for raw_permission in permissions:
        permission = _safe_permission(raw_permission)
        if permission is None:
            return None
        permission_set.add(permission)
    is_admin, is_superuser = derive_auth_flags(frozenset(role_set))
    return AuthUser(
        id=uid,
        role_codes=frozenset(role_set),
        permission_codes=frozenset(permission_set),
        is_active=is_active,
        is_superuser=is_superuser,
        is_admin=is_admin,
        email=email if isinstance(email, str) else None,
    )


def _safe_role(raw: object) -> RoleCode | None:
    if not isinstance(raw, str):
        return None
    return raw


def _safe_permission(raw: object) -> PermissionCode | None:
    if not isinstance(raw, str):
        return None
    try:
        return PermissionCode(raw)
    except ValueError:
        return None


def _to_str_key_dict(value: object) -> dict[str, object] | None:
    if not _is_mapping(value):
        return None
    out: dict[str, object] = {}
    for key, item in value.items():
        out[str(key)] = item
    return out


def _is_mapping(value: object) -> TypeGuard[Mapping[object, object]]:
    return isinstance(value, Mapping)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)
