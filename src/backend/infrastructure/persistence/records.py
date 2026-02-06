from __future__ import annotations

import msgspec
from uuid_utils.compat import UUID

from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.login import Login
from backend.domain.core.value_objects.identity.username import Username
from backend.domain.core.value_objects.password import Password


class UserRowRecord(msgspec.Struct, frozen=True):
    id: UUID
    email: Email
    login: Login
    username: Username
    password_hash: Password
    is_active: bool


class UserRoleCodeRecord(msgspec.Struct, frozen=True):
    user_id: UUID
    role: str
