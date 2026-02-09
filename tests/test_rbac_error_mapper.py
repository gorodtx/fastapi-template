from __future__ import annotations

from uuid_utils.compat import UUID

from backend.application.common.exceptions.application import (
    AppError,
)
from backend.application.common.exceptions.error_mappers.rbac import (
    map_role_change_error,
    map_role_input_error,
)
from backend.domain.core.constants.rbac import RoleAction
from backend.domain.core.exceptions.rbac import (
    LastSuperAdminRemovalError,
    RoleAlreadyAssignedError,
    RoleNotAssignedError,
    RoleSelfModificationError,
)
from backend.domain.core.value_objects.access.role_code import RoleCode

_USER_ID: UUID = UUID("00000000-0000-0000-0000-000000000001")
_ROLE_USER: RoleCode = RoleCode("user")
_ROLE_SUPER_ADMIN: RoleCode = RoleCode("super_admin")


def test_map_role_input_error_value_error_maps_to_role_unknown() -> None:
    mapped = map_role_input_error("manager")(ValueError("bad role"))

    assert isinstance(mapped, AppError)
    assert mapped.code == "rbac.role_unknown"
    assert mapped.message == "Role does not exist"
    assert mapped.detail is None


def test_map_role_input_error_not_assigned_maps_to_conflict() -> None:
    mapped = map_role_input_error("user", allow_unassigned=True)(
        RoleNotAssignedError(_ROLE_USER, _USER_ID)
    )

    assert isinstance(mapped, AppError)
    assert mapped.code == "conflict"
    assert mapped.message == "Role not assigned"
    assert mapped.detail is None


def test_map_role_change_error_already_assigned_masks_details() -> None:
    mapped = map_role_change_error(
        action=RoleAction.ASSIGN,
        target_role=_ROLE_USER,
    )(RoleAlreadyAssignedError(_ROLE_USER, _USER_ID))

    assert isinstance(mapped, AppError)
    assert mapped.code == "conflict"
    assert mapped.message == "Role already assigned"
    assert mapped.detail is None


def test_map_role_change_error_self_modification_masks_details() -> None:
    mapped = map_role_change_error(
        action=RoleAction.REVOKE,
        target_role=_ROLE_SUPER_ADMIN,
    )(RoleSelfModificationError(RoleAction.REVOKE, _USER_ID))

    assert isinstance(mapped, AppError)
    assert mapped.code == "auth.forbidden"
    assert mapped.message == "Cannot modify own roles"
    assert mapped.detail is None


def test_map_role_change_error_last_super_admin_masks_details() -> None:
    mapped = map_role_change_error(
        action=RoleAction.REVOKE,
        target_role=_ROLE_SUPER_ADMIN,
    )(LastSuperAdminRemovalError(_USER_ID))

    assert isinstance(mapped, AppError)
    assert mapped.code == "conflict"
    assert mapped.message == "Cannot remove last super_admin role"
    assert mapped.detail is None
