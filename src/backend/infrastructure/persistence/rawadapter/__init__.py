from __future__ import annotations

from backend.infrastructure.persistence.rawadapter.rbac import (
    q_get_role_ids_by_codes,
    q_get_user_role_codes,
    q_list_user_ids_by_role_id,
    q_replace_user_roles,
)
from backend.infrastructure.persistence.rawadapter.users import (
    q_delete_user,
    q_get_user_row_by_email,
    q_get_user_row_by_id,
    q_upsert_user_row,
)

__all__: list[str] = [
    "q_delete_user",
    "q_get_role_ids_by_codes",
    "q_get_user_role_codes",
    "q_get_user_row_by_email",
    "q_get_user_row_by_id",
    "q_list_user_ids_by_role_id",
    "q_replace_user_roles",
    "q_upsert_user_row",
]
