from __future__ import annotations

import re
from collections.abc import Callable
from typing import Final

from backend.application.common.exceptions.application import (
    AppError,
    ConflictError,
    UnknownRoleError,
)
from backend.application.common.exceptions.storage import StorageError

_UNIQUE_FIELDS: tuple[str, ...] = ("email", "login", "username")
_UNIQUE_CONSTRAINT_FIELD_MAP: dict[str, str] = {
    "uq_users_email": "email",
    "uq_users_login": "login",
    "uq_users_username": "username",
    "users_email_key": "email",
    "users_login_key": "login",
    "users_username_key": "username",
}
_DETAIL_CONSTRAINT_PATTERN = re.compile(
    r'constraint "(?P<constraint>[^"]+)"', re.IGNORECASE
)
_DETAIL_FIELD_PATTERN = re.compile(r"Key \((?P<field>[a-z_]+)\)=")
_DB_ERROR_PREFIX: Final[str] = "db."
_INTERNAL_ERROR_CODE: Final[str] = "internal.error"
_INTERNAL_ERROR_MESSAGE: Final[str] = "Internal server error"


def map_storage_error_to_app() -> Callable[[StorageError], AppError]:
    def mapper(error: StorageError) -> AppError:
        if error.code == "db.unique_violation":
            field = _read_unique_field(error.meta, error.detail)
            if field is None:
                return ConflictError("Resource already exists")
            return ConflictError(
                f"Resource with this {field} already exists",
                meta={"field": field},
            )
        if error.code == "rbac.seed_mismatch":
            return UnknownRoleError()
        if error.code.startswith(_DB_ERROR_PREFIX):
            return AppError(
                code=_INTERNAL_ERROR_CODE,
                message=_INTERNAL_ERROR_MESSAGE,
            )
        if error.code.endswith(".not_found"):
            return AppError(code=error.code, message=error.message)
        return AppError(code=error.code, message=error.message)

    return mapper


def _read_unique_field(
    meta: dict[str, object] | None, detail: str | None
) -> str | None:
    constraint = _read_constraint(meta, detail)
    if constraint is not None:
        mapped = _UNIQUE_CONSTRAINT_FIELD_MAP.get(constraint)
        if mapped is not None:
            return mapped
    return _read_field_from_detail(detail)


def _read_constraint(
    meta: dict[str, object] | None, detail: str | None
) -> str | None:
    if meta is None:
        return _read_constraint_from_detail(detail)
    raw_constraint: object = meta.get("constraint")
    if isinstance(raw_constraint, str):
        return raw_constraint.lower()
    return _read_constraint_from_detail(detail)


def _read_constraint_from_detail(detail: str | None) -> str | None:
    if detail is None:
        return None
    match = _DETAIL_CONSTRAINT_PATTERN.search(detail)
    if match is None:
        return None
    raw_constraint = match.group("constraint")
    return raw_constraint.lower()


def _read_field_from_detail(detail: str | None) -> str | None:
    if detail is None:
        return None
    match = _DETAIL_FIELD_PATTERN.search(detail)
    if match is None:
        return None
    raw_field = match.group("field").lower()
    for field in _UNIQUE_FIELDS:
        if field == raw_field:
            return field
    return None
