from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import uuid_utils.compat as uuid
from msgspec import to_builtins

from fastapi_backend.domain.core.entities.base import TypeID
from fastapi_backend.domain.events.base import TypeEventID


@dataclass(frozen=True, slots=True, kw_only=True)
class PermissionGrantedToRole:
    aggregate_id: TypeID
    permission: str
    event_id: TypeEventID = field(default_factory=uuid.uuid7, init=False, repr=False)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC), init=False)
    version: int = field(default=1, init=False)

    def asdict(self) -> dict[str, Any]:
        return to_builtins(self, str_keys=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class PermissionRevokedFromRole:
    aggregate_id: TypeID
    permission: str
    event_id: TypeEventID = field(default_factory=uuid.uuid7, init=False, repr=False)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC), init=False)
    version: int = field(default=1, init=False)

    def asdict(self) -> dict[str, Any]:
        return to_builtins(self, str_keys=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class UserRoleAssigned:
    aggregate_id: TypeID  # role id
    user_id: TypeID
    event_id: TypeEventID = field(default_factory=uuid.uuid7, init=False, repr=False)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC), init=False)
    version: int = field(default=1, init=False)

    def asdict(self) -> dict[str, Any]:
        return to_builtins(self, str_keys=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class UserRoleRevoked:
    aggregate_id: TypeID  # role id
    user_id: TypeID
    event_id: TypeEventID = field(default_factory=uuid.uuid7, init=False, repr=False)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC), init=False)
    version: int = field(default=1, init=False)

    def asdict(self) -> dict[str, Any]:
        return to_builtins(self, str_keys=True)
