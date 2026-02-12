from __future__ import annotations

from uuid_utils.compat import UUID

from backend.presentation.http.api.schemas.base import BaseSchema
from backend.presentation.http.api.schemas.rbac_fields import RoleCodeStr


class UserRolesResponse(BaseSchema):
    user_id: UUID
    roles: list[str]
    permissions: list[str]


class RoleChangeRequest(BaseSchema):
    role_code: RoleCodeStr
