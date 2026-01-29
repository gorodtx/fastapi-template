from __future__ import annotations

from uuid_utils.compat import UUID

from backend.presentation.http.api.schemas.base import BaseShema


class UserRolesResponse(BaseShema):
    user_id: UUID
    roles: list[str]
    permissions: list[str]


class RoleChangeRequest(BaseShema):
    role: str
