from __future__ import annotations

from backend.application.common.exceptions.application import (
    AppError,
    ConflictError,
)
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.exceptions.storage import StorageError


def test_unique_violation_masks_internal_detail() -> None:
    error = StorageError(
        code="db.unique_violation",
        message="Unique constraint violated",
        detail="INSERT ... password_hash ...",
        meta={"sqlstate": "23505", "constraint": "uq_users_email"},
    )

    mapped = map_storage_error_to_app()(error)

    assert isinstance(mapped, ConflictError)
    assert mapped.message == "Resource with this email already exists"
    assert mapped.detail is None
    assert mapped.meta == {"field": "email"}


def test_unique_violation_uses_constraint_from_detail() -> None:
    error = StorageError(
        code="db.unique_violation",
        message="Unique constraint violated",
        detail='duplicate key value violates unique constraint "uq_users_login"\n'
        "DETAIL:  Key (login)=(taken) already exists.",
        meta={"sqlstate": "23505"},
    )

    mapped = map_storage_error_to_app()(error)

    assert isinstance(mapped, ConflictError)
    assert mapped.message == "Resource with this login already exists"
    assert mapped.detail is None
    assert mapped.meta == {"field": "login"}


def test_non_unique_storage_error_keeps_original_payload() -> None:
    error = StorageError(
        code="db.error",
        message="Database error",
        detail="connection refused",
        meta={"sqlstate": "08006"},
    )

    mapped = map_storage_error_to_app()(error)

    assert isinstance(mapped, AppError)
    assert mapped.code == "internal.error"
    assert mapped.message == "Internal server error"
    assert mapped.detail is None
    assert mapped.meta is None
