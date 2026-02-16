from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from http.client import HTTPConnection
from urllib.parse import urlparse

import pytest

_DEFAULT_BASE_URL = "http://127.0.0.1:8080"
_REQUEST_TIMEOUT_S = 10
_RATE_LIMIT_RETRY_S = 0.2
_RATE_LIMIT_MAX_RETRIES = 20


@dataclass(slots=True, frozen=True)
class _HttpResponse:
    status: int
    body: str


@dataclass(slots=True, frozen=True)
class _ApiTarget:
    host: str
    port: int
    base_path: str


@dataclass(slots=True, frozen=True)
class _UserSession:
    email: str
    raw_password: str
    fingerprint: str
    access_token: str
    refresh_token: str
    user_id: str
    user2_id: str


def _build_password() -> str:
    return "".join(("Strong", "Pass", "123", "!"))


def _parse_target(base_url: str) -> _ApiTarget:
    parsed = urlparse(base_url)
    if parsed.scheme != "http":
        raise AssertionError(f"Expected http:// base URL, got: {base_url!r}")
    if parsed.hostname is None:
        raise AssertionError("Base URL has no hostname")
    return _ApiTarget(
        host=parsed.hostname,
        port=parsed.port or 80,
        base_path=parsed.path.rstrip("/"),
    )


def _request(
    *,
    target: _ApiTarget,
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
    bearer_token: str | None = None,
) -> _HttpResponse:
    headers: dict[str, str] = {}
    body: str | None = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload, separators=(",", ":"))
    if bearer_token is not None:
        headers["Authorization"] = f"Bearer {bearer_token}"

    last_response: _HttpResponse | None = None
    for attempt in range(_RATE_LIMIT_MAX_RETRIES + 1):
        connection = HTTPConnection(
            host=target.host,
            port=target.port,
            timeout=_REQUEST_TIMEOUT_S,
        )
        try:
            connection.request(
                method=method,
                url=f"{target.base_path}{path}",
                body=body,
                headers=headers,
            )
            response = connection.getresponse()
            response_body = response.read().decode("utf-8")
            last_response = _HttpResponse(
                status=response.status,
                body=response_body,
            )
        finally:
            connection.close()

        if last_response.status != 429:
            return last_response
        if attempt < _RATE_LIMIT_MAX_RETRIES:
            time.sleep(_RATE_LIMIT_RETRY_S)

    if last_response is None:
        raise RuntimeError("HTTP request did not produce a response")
    return last_response


def _parse_json_object(raw_body: str) -> dict[str, object]:
    payload = json.loads(raw_body)
    if not isinstance(payload, dict):
        raise AssertionError("Expected JSON object")
    parsed: dict[str, object] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise AssertionError("Expected string JSON keys")
        parsed[key] = value
    return parsed


def _require_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise AssertionError(f"Expected string field: {key}")
    return value


def _expected_openapi_paths() -> set[str]:
    return {
        "/auth/login",
        "/auth/logout",
        "/auth/refresh",
        "/auth/register",
        "/rbac/users/{user_id}/roles",
        "/rbac/users/{user_id}/roles/{role_code}",
        "/system",
        "/users",
        "/users/me",
        "/users/{user_id}",
    }


def _assert_api_available(target: _ApiTarget) -> None:
    try:
        response = _request(target=target, method="GET", path="/openapi.json")
    except OSError as exc:
        pytest.skip(f"Live API is unavailable: {exc}")
    if response.status != 200:
        pytest.skip(
            f"Live API is unavailable: /openapi.json returned {response.status}"
        )


def _assert_public_routes_and_openapi(
    target: _ApiTarget,
) -> set[str]:
    response = _request(target=target, method="GET", path="/openapi.json")
    assert response.status == 200
    payload = _parse_json_object(response.body)
    raw_paths = payload.get("paths")
    assert isinstance(raw_paths, dict)
    actual_paths = {path for path in raw_paths if isinstance(path, str)}
    assert actual_paths == _expected_openapi_paths()

    assert _request(target=target, method="GET", path="/docs").status == 200
    system_response = _request(target=target, method="GET", path="/system")
    assert system_response.status == 200
    system_payload = _parse_json_object(system_response.body)
    assert _require_str(system_payload, "status") == "ok"
    checks = system_payload.get("checks")
    assert isinstance(checks, dict)
    assert checks.get("db") == "ok"
    assert checks.get("redis") == "ok"
    assert (
        _request(target=target, method="GET", path="/users/me").status == 401
    )
    assert _request(target=target, method="POST", path="/system").status == 405
    assert (
        _request(target=target, method="GET", path="/auth/login").status == 405
    )
    assert (
        _request(target=target, method="GET", path="/auth/register").status
        == 405
    )
    assert _request(target=target, method="GET", path="/users").status == 405
    assert (
        _request(
            target=target,
            method="GET",
            path="/this-path-does-not-exist",
        ).status
        == 404
    )

    return {"/system", "/users/me"}


def _run_auth_flow(target: _ApiTarget) -> tuple[_UserSession, set[str]]:
    seed = str(int(time.time() * 1000))
    login = f"e2e{seed}"
    email = f"{login}@example.com"
    raw_password = _build_password()
    fingerprint = f"fp-{seed}-device"
    covered = {
        "/auth/register",
        "/auth/login",
        "/auth/refresh",
        "/auth/logout",
    }

    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/register",
            payload={"email": "a@b.c"},
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/register",
            payload={
                "email": email,
                "login": login,
                "username": login,
                "raw_password": raw_password,
                "fingerprint": "@@@",
            },
        ).status
        == 422
    )

    register_ok = _request(
        target=target,
        method="POST",
        path="/auth/register",
        payload={
            "email": email,
            "login": login,
            "username": login,
            "raw_password": raw_password,
            "fingerprint": fingerprint,
        },
    )
    assert register_ok.status == 200
    register_payload = _parse_json_object(register_ok.body)
    access_token = _require_str(register_payload, "access_token")
    refresh_token = _require_str(register_payload, "refresh_token")

    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/register",
            payload={
                "email": email,
                "login": login,
                "username": login,
                "raw_password": raw_password,
                "fingerprint": fingerprint,
            },
        ).status
        == 409
    )

    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/login",
            payload={
                "login": login,
                "raw_password": raw_password,
                "fingerprint": fingerprint,
            },
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/login",
            payload={
                "email": email,
                "raw_password": "WrongPass!",
                "fingerprint": fingerprint,
            },
        ).status
        == 401
    )

    login_ok = _request(
        target=target,
        method="POST",
        path="/auth/login",
        payload={
            "email": email,
            "raw_password": raw_password,
            "fingerprint": fingerprint,
        },
    )
    assert login_ok.status == 200
    login_payload = _parse_json_object(login_ok.body)
    access_token = _require_str(login_payload, "access_token")
    refresh_token = _require_str(login_payload, "refresh_token")

    me_response = _request(
        target=target,
        method="GET",
        path="/users/me",
        bearer_token=access_token,
    )
    assert me_response.status == 200
    user_payload = _parse_json_object(me_response.body)
    user_id = _require_str(user_payload, "id")

    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/refresh",
            payload={
                "refresh_token": "invalid",
                "fingerprint": fingerprint,
            },
        ).status
        == 401
    )

    refresh_ok = _request(
        target=target,
        method="POST",
        path="/auth/refresh",
        payload={
            "refresh_token": refresh_token,
            "fingerprint": fingerprint,
        },
    )
    assert refresh_ok.status == 200
    old_refresh_token = refresh_token
    refresh_payload = _parse_json_object(refresh_ok.body)
    access_token = _require_str(refresh_payload, "access_token")
    refresh_token = _require_str(refresh_payload, "refresh_token")

    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/refresh",
            payload={
                "refresh_token": old_refresh_token,
                "fingerprint": fingerprint,
            },
        ).status
        == 401
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/logout",
            payload={
                "refresh_token": refresh_token,
                "fingerprint": fingerprint,
            },
        ).status
        == 401
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/logout",
            payload={
                "refresh_token": refresh_token,
                "fingerprint": fingerprint,
            },
            bearer_token=access_token,
        ).status
        == 200
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/refresh",
            payload={
                "refresh_token": refresh_token,
                "fingerprint": fingerprint,
            },
        ).status
        == 401
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/refresh",
            payload={
                "refresh_token": refresh_token,
                "fingerprint": "other-device-12345",
            },
        ).status
        == 401
    )

    return (
        _UserSession(
            email=email,
            raw_password=raw_password,
            fingerprint=fingerprint,
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
            user2_id=user_id,
        ),
        covered | {"/users/me"},
    )


def _run_users_and_rbac_forbidden_flow(
    target: _ApiTarget,
    session: _UserSession,
) -> set[str]:
    assert (
        _request(
            target=target,
            method="POST",
            path="/users",
            payload={"email": "bad"},
            bearer_token=session.access_token,
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/users",
            payload={
                "email": "created1@example.com",
                "login": "created1",
                "username": "created1",
                "raw_password": session.raw_password,
            },
            bearer_token=session.access_token,
        ).status
        == 403
    )
    assert (
        _request(
            target=target,
            method="PATCH",
            path=f"/users/{session.user2_id}",
            payload={},
            bearer_token=session.access_token,
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="PATCH",
            path=f"/users/{session.user2_id}",
            payload={"email": "newmail@example.com"},
            bearer_token=session.access_token,
        ).status
        == 403
    )
    assert (
        _request(
            target=target,
            method="DELETE",
            path=f"/users/{session.user2_id}",
            bearer_token=session.access_token,
        ).status
        == 403
    )

    assert (
        _request(
            target=target,
            method="GET",
            path=f"/rbac/users/{session.user2_id}/roles",
        ).status
        == 401
    )
    assert (
        _request(
            target=target,
            method="GET",
            path=f"/rbac/users/{session.user2_id}/roles",
            bearer_token=session.access_token,
        ).status
        == 403
    )
    assert (
        _request(
            target=target,
            method="POST",
            path=f"/rbac/users/{session.user2_id}/roles",
            payload={"role_code": "admin"},
            bearer_token=session.access_token,
        ).status
        == 403
    )
    assert (
        _request(
            target=target,
            method="DELETE",
            path=f"/rbac/users/{session.user2_id}/roles/admin",
            bearer_token=session.access_token,
        ).status
        == 403
    )
    return {
        "/users",
        "/users/{user_id}",
        "/rbac/users/{user_id}/roles",
        "/rbac/users/{user_id}/roles/{role_code}",
    }


def _run_missing_and_validation_flow(
    target: _ApiTarget,
    session: _UserSession,
) -> set[str]:
    missing_user_id = "00000000-0000-7000-8000-000000000001"
    assert (
        _request(
            target=target,
            method="PATCH",
            path=f"/users/{missing_user_id}",
            payload={"email": "x@example.com"},
            bearer_token=session.access_token,
        ).status
        == 403
    )
    assert (
        _request(
            target=target,
            method="DELETE",
            path=f"/users/{missing_user_id}",
            bearer_token=session.access_token,
        ).status
        == 403
    )
    assert (
        _request(
            target=target,
            method="GET",
            path=f"/rbac/users/{missing_user_id}/roles",
            bearer_token=session.access_token,
        ).status
        == 403
    )
    assert (
        _request(
            target=target,
            method="POST",
            path=f"/rbac/users/{session.user2_id}/roles",
            payload={"role_code": "@@@"},
            bearer_token=session.access_token,
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="DELETE",
            path=f"/rbac/users/{session.user2_id}/roles/@@@",
            bearer_token=session.access_token,
        ).status
        == 422
    )
    return {
        "/users/{user_id}",
        "/rbac/users/{user_id}/roles",
        "/rbac/users/{user_id}/roles/{role_code}",
    }


def _run_additional_hardening_flow(
    target: _ApiTarget,
    session: _UserSession,
) -> set[str]:
    seed = str(int(time.time() * 1000))
    login = f"hard{seed}"
    email = f"{login}@example.com"

    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/register",
            payload={
                "email": email,
                "login": login,
                "username": login,
                "raw_password": "short",
                "fingerprint": f"fp-{seed}-device",
            },
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/register",
            payload={
                "email": email,
                "login": login,
                "username": login,
                "raw_password": _build_password(),
                "fingerprint": f"fp-{seed}-device",
                "extra": "forbidden",
            },
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/login",
            payload={
                "email": session.email,
                "raw_password": session.raw_password,
                "fingerprint": session.fingerprint,
                "extra": "forbidden",
            },
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/login",
            payload={
                "email": session.email,
                "raw_password": session.raw_password,
            },
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/refresh",
            payload={"refresh_token": "invalid"},
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/refresh",
            payload={
                "refresh_token": "invalid",
                "fingerprint": "@@@",
            },
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/logout",
            payload={
                "fingerprint": session.fingerprint,
            },
            bearer_token=session.access_token,
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/auth/logout",
            payload={
                "refresh_token": "invalid",
                "fingerprint": "@@@",
            },
            bearer_token=session.access_token,
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path="/users",
            payload={
                "email": f"noauth_{seed}@example.com",
                "login": f"noauth{seed}",
                "username": f"noauth{seed}",
                "raw_password": _build_password(),
            },
        ).status
        == 401
    )
    assert (
        _request(
            target=target,
            method="PATCH",
            path=f"/users/{session.user_id}",
            payload={"email": "newmail@example.com", "extra": "forbidden"},
            bearer_token=session.access_token,
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path=f"/rbac/users/{session.user_id}/roles",
            payload={},
            bearer_token=session.access_token,
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="POST",
            path=f"/rbac/users/{session.user_id}/roles",
            payload={"role_code": "user", "extra": "forbidden"},
            bearer_token=session.access_token,
        ).status
        == 422
    )
    assert (
        _request(
            target=target,
            method="DELETE",
            path=f"/rbac/users/{session.user_id}/roles/USER",
            bearer_token=session.access_token,
        ).status
        == 422
    )

    return {
        "/system",
        "/auth/register",
        "/auth/login",
        "/auth/refresh",
        "/auth/logout",
        "/users",
        "/users/{user_id}",
        "/rbac/users/{user_id}/roles",
        "/rbac/users/{user_id}/roles/{role_code}",
    }


def _run_optional_admin_flow(target: _ApiTarget, seed: str) -> set[str]:
    admin_bearer = os.getenv("E2E_ADMIN_BEARER")
    if admin_bearer is None or not admin_bearer:
        return set()

    password = _build_password()
    create_response = _request(
        target=target,
        method="POST",
        path="/users",
        payload={
            "email": f"admin_{seed}@example.com",
            "login": f"admin_{seed}",
            "username": f"admin_{seed}",
            "raw_password": password,
        },
        bearer_token=admin_bearer,
    )
    assert create_response.status == 200
    created_payload = _parse_json_object(create_response.body)
    created_user_id = _require_str(created_payload, "id")

    assert (
        _request(
            target=target,
            method="PATCH",
            path=f"/users/{created_user_id}",
            payload={"email": f"admin_{seed}_2@example.com"},
            bearer_token=admin_bearer,
        ).status
        == 200
    )
    assert (
        _request(
            target=target,
            method="GET",
            path=f"/rbac/users/{created_user_id}/roles",
            bearer_token=admin_bearer,
        ).status
        == 200
    )
    assert (
        _request(
            target=target,
            method="POST",
            path=f"/rbac/users/{created_user_id}/roles",
            payload={"role_code": "user"},
            bearer_token=admin_bearer,
        ).status
        == 200
    )
    assert (
        _request(
            target=target,
            method="DELETE",
            path=f"/rbac/users/{created_user_id}/roles/user",
            bearer_token=admin_bearer,
        ).status
        == 200
    )
    assert (
        _request(
            target=target,
            method="DELETE",
            path=f"/users/{created_user_id}",
            bearer_token=admin_bearer,
        ).status
        == 200
    )
    return {
        "/users",
        "/users/{user_id}",
        "/rbac/users/{user_id}/roles",
        "/rbac/users/{user_id}/roles/{role_code}",
    }


def test_live_endpoint_matrix_all_paths() -> None:
    if os.getenv("RUN_LIVE_E2E") != "1":
        pytest.skip("Set RUN_LIVE_E2E=1 to run live endpoint matrix checks")

    target = _parse_target(os.getenv("E2E_BASE_URL", _DEFAULT_BASE_URL))
    _assert_api_available(target)

    covered = set()
    covered |= _assert_public_routes_and_openapi(target)
    session, auth_covered = _run_auth_flow(target)
    covered |= auth_covered
    covered |= _run_users_and_rbac_forbidden_flow(target, session)
    covered |= _run_missing_and_validation_flow(target, session)
    covered |= _run_additional_hardening_flow(target, session)
    covered |= _run_optional_admin_flow(target, seed=str(int(time.time())))

    final_me = _request(
        target=target,
        method="GET",
        path="/users/me",
        bearer_token=session.access_token,
    )
    assert final_me.status == 200
    final_payload = _parse_json_object(final_me.body)
    assert _require_str(final_payload, "id") == session.user_id

    assert covered == _expected_openapi_paths()
