from __future__ import annotations

from enum import StrEnum


class SystemRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


class UserState(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
