from __future__ import annotations

from uuid_utils.compat import UUID

from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.handlers.result import Err, Result, ResultImpl
from backend.domain.core.entities.user import User
from backend.domain.core.types.rbac import PermissionCode


async def fetch_user_and_permissions(
    gateway: PersistenceGateway, user_id: UUID
) -> Result[tuple[User, set[PermissionCode]], AppError]:
    map_storage_error = map_storage_error_to_app()
    user_result = (await gateway.users.get_by_id(user_id)).map_err(
        map_storage_error
    )
    if isinstance(user_result, Err):
        return ResultImpl.err_from(user_result)

    permissions_result = (
        await gateway.rbac.get_user_permission_codes(user_id)
    ).map_err(map_storage_error)
    if isinstance(permissions_result, Err):
        return ResultImpl.err_from(permissions_result)

    return ResultImpl.ok((user_result.value, permissions_result.value))
