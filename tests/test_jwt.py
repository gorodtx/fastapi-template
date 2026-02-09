from __future__ import annotations

from datetime import timedelta

from jwt import decode as jwt_decode
from uuid_utils.compat import UUID

from backend.infrastructure.security.auth.jwt import JwtConfig, JwtImpl

_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _config() -> JwtConfig:
    secret = "".join(("test", "-", "secret"))
    return JwtConfig(
        issuer="template",
        audience="template",
        alg="HS256",
        access_ttl=timedelta(minutes=15),
        refresh_ttl=timedelta(days=14),
        secret=secret,
    )


def test_issue_refresh_returns_token_and_jti() -> None:
    jwt_impl = JwtImpl(cfg=_config())

    token, jti = jwt_impl.issue_refresh(user_id=_USER_ID, fingerprint="fp")

    payload = jwt_decode(
        token,
        jwt_impl.cfg.secret,
        algorithms=[jwt_impl.cfg.alg],
        audience=jwt_impl.cfg.audience,
        issuer=jwt_impl.cfg.issuer,
    )
    assert isinstance(jti, str)
    assert jti
    assert payload["jti"] == jti
    assert payload["sub"] == str(_USER_ID)
    assert payload["fpr"] == "fp"


def test_issue_refresh_produces_unique_token_and_jti() -> None:
    jwt_impl = JwtImpl(cfg=_config())

    token_1, jti_1 = jwt_impl.issue_refresh(user_id=_USER_ID, fingerprint="fp")
    token_2, jti_2 = jwt_impl.issue_refresh(user_id=_USER_ID, fingerprint="fp")

    assert jti_1 != jti_2
    assert token_1 != token_2


def test_verify_refresh_returns_user_fingerprint_and_jti() -> None:
    jwt_impl = JwtImpl(cfg=_config())
    token, issued_jti = jwt_impl.issue_refresh(
        user_id=_USER_ID, fingerprint="fp"
    )

    verified = jwt_impl.verify_refresh(token).unwrap()

    assert verified == (_USER_ID, "fp", issued_jti)


def test_verify_access_invalid_token_returns_generic_message() -> None:
    jwt_impl = JwtImpl(cfg=_config())

    err = jwt_impl.verify_access("not-a-jwt").unwrap_err()

    assert err.code == "auth.unauthenticated"
    assert err.message == "Invalid access token"


def test_verify_refresh_invalid_token_returns_generic_message() -> None:
    jwt_impl = JwtImpl(cfg=_config())

    err = jwt_impl.verify_refresh("not-a-jwt").unwrap_err()

    assert err.code == "auth.unauthenticated"
    assert err.message == "Invalid refresh token"
