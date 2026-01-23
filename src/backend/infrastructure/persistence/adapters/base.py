from __future__ import annotations

from backend.application.common.exceptions.storage import NotFoundStorageError, StorageError
from backend.application.common.interfaces.ports.persistence.manager import TransactionManager


class UnboundAdapter:
    __slots__ = ("_manager",)

    def __init__(self, manager: TransactionManager) -> None:
        self._manager = manager

    @property
    def manager(self) -> TransactionManager:
        return self._manager

    @staticmethod
    def require_found[T](
        value: T | None,
        *,
        code: str,
        message: str,
        detail: str,
    ) -> T:
        if value is None:
            raise NotFoundStorageError(code=code, message=message, detail=detail)
        return value

    @staticmethod
    def require_condition(
        ok: bool,
        *,
        code: str,
        message: str,
        detail: str | None = None,
    ) -> None:
        if not ok:
            raise StorageError(code=code, message=message, detail=detail)


class BoundAdapter[E](UnboundAdapter):
    __slots__ = ("_record_type",)

    def __init__(self, manager: TransactionManager, record_type: type[E]) -> None:
        super().__init__(manager)
        self._record_type = record_type

    @property
    def record_type(self) -> type[E]:
        return self._record_type
