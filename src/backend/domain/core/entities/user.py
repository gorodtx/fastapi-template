from __future__ import annotations

from dataclasses import dataclass, field

from uuid_utils.compat import UUID

from backend.domain.core.types.rbac import RoleCode


@dataclass(kw_only=True)
class User:
    id: UUID
    email: str
    login: str
    username: str
    password: str
    is_active: bool = True
    roles: set[RoleCode] = field(default_factory=set)
