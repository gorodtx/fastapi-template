from __future__ import annotations

from sqlalchemy.exc import DBAPIError

from backend.infrastructure.errors.sqlalchemy_errors import map_dbapi_error


class _OrigDbError(Exception):
    def __init__(
        self: _OrigDbError,
        *,
        pgcode: str | None = None,
        sqlstate: str | None = None,
    ) -> None:
        super().__init__("db boom")
        self.pgcode = pgcode
        self.sqlstate = sqlstate


def _make_dbapi_error(sqlstate: str) -> DBAPIError:
    return DBAPIError(
        statement="SELECT 1",
        params={},
        orig=_OrigDbError(pgcode=sqlstate),
        hide_parameters=False,
    )


def test_map_dbapi_error_marks_serialization_failure_as_transient() -> None:
    mapped = map_dbapi_error(_make_dbapi_error("40001"))

    assert mapped.code == "db.transient.serialization_failure"
    assert mapped.message == "Temporary database error"
    assert mapped.meta == {"sqlstate": "40001"}


def test_map_dbapi_error_marks_deadlock_as_transient() -> None:
    mapped = map_dbapi_error(_make_dbapi_error("40P01"))

    assert mapped.code == "db.transient.deadlock_detected"
    assert mapped.message == "Temporary database error"
    assert mapped.meta == {"sqlstate": "40P01"}


def test_map_dbapi_error_marks_lock_not_available_as_transient() -> None:
    mapped = map_dbapi_error(_make_dbapi_error("55P03"))

    assert mapped.code == "db.transient.lock_not_available"
    assert mapped.message == "Temporary database error"
    assert mapped.meta == {"sqlstate": "55P03"}


def test_map_dbapi_error_keeps_non_transient_as_generic_db_error() -> None:
    mapped = map_dbapi_error(_make_dbapi_error("08006"))

    assert mapped.code == "db.error"
    assert mapped.message == "Database error"
    assert mapped.meta == {"sqlstate": "08006"}
