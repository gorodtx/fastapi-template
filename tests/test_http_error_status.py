from __future__ import annotations

from backend.presentation.app import _status_for_code


def test_auth_and_rbac_codes_map_to_expected_http_statuses() -> None:
    assert _status_for_code("auth.unauthenticated") == 401
    assert _status_for_code("auth.forbidden") == 403
    assert _status_for_code("rbac.hierarchy_violation") == 403
    assert _status_for_code("rbac.role_unknown") == 409


def test_conflict_not_found_and_fallback_statuses() -> None:
    assert _status_for_code("conflict") == 409
    assert _status_for_code("auth.too_many_requests") == 429
    assert _status_for_code("user.not_found") == 404
    assert _status_for_code("unexpected.error") == 400
