from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:

    class BaseModel:
        def __init__(self, **_data: object) -> None: ...
else:
    from pydantic import BaseModel

from uuid_utils.compat import UUID


class UserRolesResponse(BaseModel):
    user_id: UUID
    roles: list[str]
    permissions: list[str]
