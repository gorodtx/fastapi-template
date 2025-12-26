from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import Final, Protocol, Self, cast

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.common.exceptions.db import ConstraintViolationError
from backend.application.common.interfaces.persistence.rbac import RbacPort
from backend.application.common.interfaces.persistence.users import UsersPort
from backend.infrastructure.persistence.repositories.rbac import RbacRepo
from backend.infrastructure.persistence.repositories.users import UsersRepo
from backend.infrastructure.tools.constraint_messages import ConstraintMessageProvider

_UNIQUE_VIOLATION_SQLSTATE: Final[str] = "23505"


@dataclass(frozen=True, slots=True)
class _DbViolation:
    sqlstate: str
    constraint: str


def _parse_unique_violation(err: IntegrityError) -> _DbViolation | None:
    orig = cast(_IntegrityErrorOrigin | None, getattr(err, "orig", None))
    if orig is None:
        return None

    sqlstate = orig.pgcode or orig.sqlstate
    if sqlstate != _UNIQUE_VIOLATION_SQLSTATE:
        return None

    diag = orig.diag
    constraint = (diag.constraint_name if diag is not None else None) or orig.constraint_name

    if not constraint:
        return None

    return _DbViolation(sqlstate=sqlstate, constraint=constraint)


class _ConstraintInfo(Protocol):
    constraint_name: str | None


class _IntegrityErrorOrigin(Protocol):
    pgcode: str | None
    sqlstate: str | None
    constraint_name: str | None
    diag: _ConstraintInfo | None


class SQLAlchemyUnitOfWork:
    def __init__(
        self,
        session: AsyncSession,
        msg_provider: ConstraintMessageProvider,
    ) -> None:
        self._session: AsyncSession = session
        self._msg_provider: ConstraintMessageProvider = msg_provider
        self._users_repo: UsersPort = UsersRepo(session)
        self._rbac_repo: RbacPort = RbacRepo(session)

    @property
    def users(self) -> UsersPort:
        return self._users_repo

    @property
    def rbac(self) -> RbacPort:
        return self._rbac_repo

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError as err:
            violation = _parse_unique_violation(err)
            if violation is not None:
                field, message = self._msg_provider.resolve(violation.constraint)
                raise ConstraintViolationError(
                    constraint=violation.constraint,
                    message=message,
                    field=field,
                ) from err

            raise

    async def rollback(self) -> None:
        await self._session.rollback()

    async def flush(self) -> None:
        await self._session.flush()
