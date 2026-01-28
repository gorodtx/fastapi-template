from __future__ import annotations

from backend.application.common.exceptions.error_mappers.auth import (
    map_auth_error,
    map_invalid_credentials,
    map_invalid_refresh,
    map_refresh_replay,
    unauthenticated,
)
from backend.application.common.exceptions.error_mappers.rbac import (
    map_role_input_error,
)
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.exceptions.error_mappers.users import (
    map_user_input_error,
)

__all__: list[str] = [
    "map_auth_error",
    "map_invalid_credentials",
    "map_invalid_refresh",
    "map_refresh_replay",
    "map_role_input_error",
    "map_storage_error_to_app",
    "map_user_input_error",
    "unauthenticated",
]
