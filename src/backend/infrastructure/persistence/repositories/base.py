from __future__ import annotations

from collections.abc import Mapping, Sequence

from sqlalchemy import delete, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from backend.domain.core.entities.base import TypeID


class BaseRepository[TModel]:
    _model_class: type[TModel]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_or_raise(self, entity_id: TypeID) -> TModel:
        model = await self._session.get(self._model_class, entity_id)
        if model is None:
            model_name = self._model_class.__name__
            raise LookupError(f"{model_name} {entity_id!r} not found")
        return model

    async def _flush(self) -> None:
        await self._session.flush()

    async def _add_and_flush(self, model: TModel) -> None:
        self._session.add(model)
        await self._flush()

    async def _paginate(
        self,
        stmt: Select[tuple[TModel]],
        *,
        offset: int,
        limit: int,
    ) -> tuple[Sequence[TModel], int]:
        paginated_stmt = stmt.offset(offset).limit(limit)
        models: Sequence[TModel] = (await self._session.execute(paginated_stmt)).scalars().all()

        count_stmt: Select[tuple[int]] = select(func.count()).select_from(stmt.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())

        return models, total

    async def _delete_where(
        self,
        model_class: type[TModel],
        *,
        filters: Mapping[str, object],
    ) -> int:
        stmt = delete(model_class).filter_by(**filters).returning(literal(1))
        rows = (await self._session.execute(stmt)).all()
        return len(rows)
