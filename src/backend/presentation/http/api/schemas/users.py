from __future__ import annotations

from uuid_utils.compat import UUID

from backend.presentation.http.api.schemas.base import BaseShema


class UserCreateRequest(BaseShema):
    email: str
    login: str
    username: str
    raw_password: str


class UserResponse(BaseShema):
    id: UUID
    email: str
    login: str
    username: str
