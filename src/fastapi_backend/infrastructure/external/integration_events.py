from __future__ import annotations

from datetime import datetime
from typing import Any, Final

import uuid_utils.compat as uuid
from msgspec import Struct, to_builtins

from fastapi_backend.domain.events.base import DomainEventProtocol
from fastapi_backend.domain.events.user.email_changed import UserEmailChanged
from fastapi_backend.domain.events.user.password_changed import UserPasswordChanged
from fastapi_backend.domain.events.user.registered import UserRegistered
from fastapi_backend.domain.events.user.username_changed import UserUsernameChanged

CONTRACT_NAMES: Final[dict[Any, str]] = {
    UserRegistered: "user.registered.v1",
    UserEmailChanged: "user.email_changed.v1",
    UserUsernameChanged: "user.username_changed.v1",
    UserPasswordChanged: "user.password_changed.v1",
}


class IntegrationEvent(Struct, kw_only=True):
    id: str
    name: str
    occurred_at: datetime
    aggregate_id: str
    version: int
    payload: dict[str, Any]

    def asdict(self) -> dict[str, Any]:
        return to_builtins(self, str_keys=True)


def map_to_integration(event: DomainEventProtocol) -> IntegrationEvent:
    contract_name = CONTRACT_NAMES.get(type(event)) or f"{type(event).__name__}.v1"
    if isinstance(event, UserRegistered):
        payload = {
            "user_id": str(event.aggregate_id),
            "username": event.username,
            "email": event.email,
            "login": event.login,
        }
    elif isinstance(event, UserEmailChanged):
        payload = {
            "user_id": str(event.aggregate_id),
            "old_email": event.old_email,
            "new_email": event.new_email,
        }
    elif isinstance(event, UserUsernameChanged):
        payload = {
            "user_id": str(event.aggregate_id),
            "old_username": event.old_username,
            "new_username": event.new_username,
        }
    elif isinstance(event, UserPasswordChanged):
        payload = {
            "user_id": str(event.aggregate_id),
        }
    else:
        payload = {"aggregate_id": str(event.aggregate_id)}

    return IntegrationEvent(
        id=str(uuid.uuid7()),
        name=contract_name,
        occurred_at=event.occurred_at,
        aggregate_id=str(event.aggregate_id),
        version=event.version,
        payload=payload,
    )
