from __future__ import annotations

from sqlalchemy.exc import DBAPIError, IntegrityError

from backend.application.common.exceptions.storage import StorageError

_SQLSTATE_UNIQUE = "23505"
_SQLSTATE_FK = "23503"
_SQLSTATE_NOT_NULL = "23502"


def extract_sqlstate(err: IntegrityError | DBAPIError) -> str | None:
    orig = getattr(err, "orig", None)
    if orig is None:
        return None
    sqlstate = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
    return sqlstate if isinstance(sqlstate, str) else None


def extract_constraint(err: IntegrityError | DBAPIError) -> str | None:
    orig = getattr(err, "orig", None)
    if orig is None:
        return None
    diag = getattr(orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None) if diag is not None else None
    if not constraint:
        constraint = getattr(orig, "constraint_name", None)
    return constraint if isinstance(constraint, str) else None


def map_integrity_error(err: IntegrityError) -> StorageError:
    sqlstate = extract_sqlstate(err)
    constraint = extract_constraint(err)
    meta: dict[str, object] = {}
    if sqlstate is not None:
        meta["sqlstate"] = sqlstate
    if constraint is not None:
        meta["constraint"] = constraint

    if sqlstate == _SQLSTATE_UNIQUE:
        return StorageError(
            code="db.unique_violation",
            message="Unique constraint violated",
            detail=str(err),
            meta=meta or None,
        )
    if sqlstate == _SQLSTATE_FK:
        return StorageError(
            code="db.fk_violation",
            message="Foreign key violated",
            detail=str(err),
            meta=meta or None,
        )
    if sqlstate == _SQLSTATE_NOT_NULL:
        return StorageError(
            code="db.not_null_violation",
            message="Not-null constraint violated",
            detail=str(err),
            meta=meta or None,
        )

    return StorageError(
        code="db.integrity_error",
        message="Integrity error",
        detail=str(err),
        meta=meta or None,
    )


def map_dbapi_error(err: DBAPIError) -> StorageError:
    sqlstate = extract_sqlstate(err)
    meta: dict[str, object] | None = None
    if sqlstate is not None:
        meta = {"sqlstate": sqlstate}
    return StorageError(
        code="db.error",
        message="Database error",
        detail=str(err),
        meta=meta,
    )
