from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.common.dtos.rbac import (
    ListRolesDTO,
    ListRolesResponseDTO,
    RoleResponseDTO,
)
from backend.domain.core.entities.base import TypeID
from backend.domain.core.entities.role import Role
from backend.domain.core.value_objects.access.permission_code import PermissionCode
from backend.domain.core.value_objects.identity.role_name import RoleName
from backend.infrastructure.persistence.sqlalchemy.models import (
    RoleModel,
    RolePermissionModel,
    UserRoleModel,
)


class RbacRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    # region helpers

    async def _load_permissions_for_roles(
        self,
        role_ids: Sequence[TypeID],
    ) -> dict[TypeID, list[str]]:
        if not role_ids:
            return {}

        stmt = select(
            RolePermissionModel.role_id,
            RolePermissionModel.code,
        ).where(RolePermissionModel.role_id.in_(role_ids))

        rows = (await self._session.execute(stmt)).all()

        result: dict[TypeID, list[str]] = {role_id: [] for role_id in role_ids}
        for role_id, code in rows:
            result[role_id].append(str(code))

        return result

    async def _count_users_for_roles(
        self,
        role_ids: Sequence[TypeID],
    ) -> dict[TypeID, int]:
        if not role_ids:
            return {}

        stmt = (
            select(
                UserRoleModel.role_id,
                func.count(UserRoleModel.user_id),
            )
            .where(UserRoleModel.role_id.in_(role_ids))
            .group_by(UserRoleModel.role_id)
        )

        rows = (await self._session.execute(stmt)).all()

        result: dict[TypeID, int] = dict.fromkeys(role_ids, 0)
        for role_id, cnt in rows:
            result[role_id] = int(cnt)

        return result

    async def _to_dto_many(self, models: Sequence[RoleModel]) -> list[RoleResponseDTO]:
        if not models:
            return []

        role_ids = [m.id for m in models]

        perms_map = await self._load_permissions_for_roles(role_ids)
        users_map = await self._count_users_for_roles(role_ids)

        return [
            RoleResponseDTO(
                id=model.id,
                name=model.name,
                description=model.description,
                permissions=perms_map.get(model.id, []),
                user_count=users_map.get(model.id, 0),
            )
            for model in models
        ]

    async def _to_dto_one(self, model: RoleModel) -> RoleResponseDTO:
        dtos = await self._to_dto_many([model])
        return dtos[0]

    # endregion

    async def create_role(self, role: Role) -> RoleResponseDTO:
        model = RoleModel(
            id=role.id,
            name=role.name.value,
            description=getattr(role, "description", None),
        )
        self._session.add(model)

        for perm in role.permissions:
            perm_model = RolePermissionModel(role_id=role.id, code=perm.value)
            self._session.add(perm_model)

        await self._session.flush()

        return await self._to_dto_one(model)

    async def update_role_name(self, *, role_id: TypeID, name: RoleName) -> RoleResponseDTO:
        model = await self._session.get(RoleModel, role_id)
        if model is None:
            raise LookupError(f"Role {role_id!r} not found")

        model.name = name.value
        await self._session.flush()

        return await self._to_dto_one(model)

    async def delete_role(self, *, role_id: TypeID) -> RoleResponseDTO:
        model = await self._session.get(RoleModel, role_id)
        if model is None:
            raise LookupError(f"Role {role_id!r} not found")

        dto = await self._to_dto_one(model)

        await self._session.execute(
            delete(RolePermissionModel).where(RolePermissionModel.role_id == role_id)
        )
        await self._session.execute(delete(UserRoleModel).where(UserRoleModel.role_id == role_id))
        await self._session.delete(model)
        await self._session.flush()

        return dto

    async def get_role(self, *, role_id: TypeID) -> RoleResponseDTO:
        model = await self._session.get(RoleModel, role_id)
        if model is None:
            raise LookupError(f"Role {role_id!r} not found")

        return await self._to_dto_one(model)

    async def list_roles(self, data: ListRolesDTO) -> ListRolesResponseDTO:
        stmt = select(RoleModel).offset(data.offset).limit(data.limit)
        models: Sequence[RoleModel] = (await self._session.execute(stmt)).scalars().all()

        total_stmt = select(func.count(RoleModel.id))
        total = int((await self._session.execute(total_stmt)).scalar_one())

        roles_dto = await self._to_dto_many(models)

        return ListRolesResponseDTO(
            roles=roles_dto,
            total=total,
            limit=data.limit,
            offset=data.offset,
        )

    async def grant_permission(self, *, role_id: TypeID, perm: PermissionCode) -> RoleResponseDTO:
        model = await self._session.get(RoleModel, role_id)
        if model is None:
            raise LookupError(f"Role {role_id!r} not found")

        stmt = select(RolePermissionModel).where(
            RolePermissionModel.role_id == role_id,
            RolePermissionModel.code == perm.value,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is None:
            self._session.add(RolePermissionModel(role_id=role_id, code=perm.value))
            await self._session.flush()

        return await self._to_dto_one(model)

    async def revoke_permission(self, *, role_id: TypeID, perm: PermissionCode) -> RoleResponseDTO:
        model = await self._session.get(RoleModel, role_id)
        if model is None:
            raise LookupError(f"Role {role_id!r} not found")

        await self._session.execute(
            delete(RolePermissionModel).where(
                RolePermissionModel.role_id == role_id,
                RolePermissionModel.code == perm.value,
            )
        )
        await self._session.flush()

        return await self._to_dto_one(model)

    async def assign_role_to_user(self, *, user_id: TypeID, role_id: TypeID) -> RoleResponseDTO:
        model = await self._session.get(RoleModel, role_id)
        if model is None:
            raise LookupError(f"Role {role_id!r} not found")

        stmt = select(UserRoleModel).where(
            UserRoleModel.user_id == user_id,
            UserRoleModel.role_id == role_id,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is None:
            self._session.add(UserRoleModel(user_id=user_id, role_id=role_id))
            await self._session.flush()

        return await self._to_dto_one(model)

    async def revoke_role_from_user(self, *, user_id: TypeID, role_id: TypeID) -> RoleResponseDTO:
        model = await self._session.get(RoleModel, role_id)
        if model is None:
            raise LookupError(f"Role {role_id!r} not found")

        await self._session.execute(
            delete(UserRoleModel).where(
                UserRoleModel.user_id == user_id,
                UserRoleModel.role_id == role_id,
            )
        )
        await self._session.flush()

        return await self._to_dto_one(model)
