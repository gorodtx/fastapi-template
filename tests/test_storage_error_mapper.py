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


def test_not_found_storage_error_masks_detail_and_meta() -> None:
    error = StorageError(
        code="user.not_found",
        message="User not found",
        detail="id=123",
        meta={"debug": "value"},
    )

    mapped = map_storage_error_to_app()(error)

    assert isinstance(mapped, AppError)
    assert mapped.code == "user.not_found"
    assert mapped.message == "User not found"
    assert mapped.detail is None
    assert mapped.meta is None


def test_rbac_seed_mismatch_maps_to_unknown_role_without_detail() -> None:
    error = StorageError(
        code="rbac.seed_mismatch",
        message="RBAC roles are missing in DB (seed mismatch)",
        detail="missing=['manager']",
        meta={"debug": "value"},
    )

    mapped = map_storage_error_to_app()(error)

    assert isinstance(mapped, AppError)
    assert mapped.code == "rbac.role_unknown"
    assert mapped.message == "Role does not exist"
    assert mapped.detail is None
    assert mapped.meta is None
