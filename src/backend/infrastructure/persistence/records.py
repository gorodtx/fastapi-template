from __future__ import annotations

import msgspec
from uuid_utils.compat import UUID


class UserRowRecord(msgspec.Struct, frozen=True):
    id: UUID
    email: str
    login: str
    username: str
    password_hash: str
    is_active: bool


class UserRoleCodeRecord(msgspec.Struct, frozen=True):
    user_id: UUID
    role: str
