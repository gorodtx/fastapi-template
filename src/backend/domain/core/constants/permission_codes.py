from __future__ import annotations

from typing import Final

from backend.domain.core.types.rbac import PermissionCode

ALL_PERMISSION_CODES: Final[frozenset[PermissionCode]] = frozenset(
    PermissionCode
)

__all__: tuple[str, ...] = ("ALL_PERMISSION_CODES",)
