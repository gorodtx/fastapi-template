from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self, runtime_checkable

from backend.application.common.interfaces.persistence.rbac import RbacPort
from backend.application.common.interfaces.persistence.users import UsersPort


@runtime_checkable
class UnitOfWorkPort(Protocol):
    @property
    def users(self) -> UsersPort: ...

    @property
    def rbac(self) -> RbacPort: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def flush(self) -> None: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
