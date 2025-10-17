from __future__ import annotations

from typing import Any, Protocol

from fastapi_backend.domain.ports.repositories.user_repository import UserRepositoryPort


class UnitOfWorkPort(Protocol):
    async def __aenter__(self) -> Any: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def flush(self) -> None: ...


class RepositoryProvider(Protocol):
    @property
    def users(self) -> UserRepositoryPort: ...
