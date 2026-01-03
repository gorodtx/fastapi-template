from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from backend.domain.core.entities.base import TypeID


class BaseRepository[TEntity]:
    __slots__ = ("_session", "entity")

    def __init__(self, session: AsyncSession, entity: type[TEntity]) -> None:
        self._session = session
        self.entity = entity

    async def add(self, entity: TEntity) -> None:
        self._session.add(entity)

    async def get(self, entity_id: TypeID) -> TEntity | None:
        return await self._session.get(self.entity, entity_id)

    async def delete(self, entity: TEntity) -> None:
        self._session.sync_session.delete(entity)

    async def _flush(self) -> None:
        await self._session.flush()

    async def _paginate(
        self,
        stmt: Select[tuple[TEntity]],
        *,
        offset: int,
        limit: int,
    ) -> tuple[Sequence[TEntity], int]:
        paginated_stmt = stmt.offset(offset).limit(limit)
        models: Sequence[TEntity] = (await self._session.execute(paginated_stmt)).scalars().all()

        count_stmt: Select[tuple[int]] = select(func.count()).select_from(stmt.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())

        return models, total
