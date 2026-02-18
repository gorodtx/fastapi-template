from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final
from uuid import uuid4

from jwt import PyJWTError
from jwt import decode as _jwt_decode_impl
from jwt import encode as _jwt_encode_impl
from uuid_utils.compat import UUID

from backend.application.common.exceptions.application import (
    AppError,
    UnauthenticatedError,
)
from backend.application.common.interfaces.auth.ports import (
    JwtIssuer,
    JwtVerifier,
)
from backend.application.handlers.result import Result, ResultImpl

_REQUIRED_CLAIMS: Final[list[str]] = ["exp", "iat", "sub", "iss", "aud"]
_ACCESS_KIND: Final[str] = "access"
_REFRESH_KIND: Final[str] = "refresh"
_ACCESS_ERROR_MESSAGE: Final[str] = "Invalid access token"
_REFRESH_ERROR_MESSAGE: Final[str] = "Invalid refresh token"


def _jwt_encode(
    payload: Mapping[str, object], key: str, *, algorithm: str
) -> str:
    payload_dict: dict[str, object] = dict(payload)
    return _jwt_encode_impl(payload_dict, key, algorithm=algorithm)


def _jwt_decode(
    token: str,
    key: str,
    *,
    algorithms: list[str],
    audience: str,
    issuer: str,
    options: dict[str, object],
) -> dict[str, object]:
    raw = _jwt_decode_impl(
        token,
        key,
        algorithms=algorithms,
        audience=audience,
        issuer=issuer,
        options=options,
    )
    if not isinstance(raw, Mapping):
        raise TypeError("Invalid token payload")
    out: dict[str, object] = {}
    for key_item, value in raw.items():
        out[str(key_item)] = value
    return out


def _access_error() -> Result[UUID, AppError]:
    return ResultImpl.err_app(UnauthenticatedError(_ACCESS_ERROR_MESSAGE))


def _refresh_error() -> Result[tuple[UUID, str, str], AppError]:
    return ResultImpl.err_app(UnauthenticatedError(_REFRESH_ERROR_MESSAGE))


def _refresh_payload(
    user_id: UUID, fingerprint: str, token_jti: str
) -> tuple[UUID, str, str]:
    return user_id, fingerprint, token_jti


@dataclass(frozen=True, slots=True)
class JwtConfig:
    issuer: str
    audience: str
    alg: str
    access_ttl: timedelta
    refresh_ttl: timedelta
    secret: str


@dataclass(frozen=True, slots=True)
class JwtImpl(JwtIssuer, JwtVerifier):
    cfg: JwtConfig

    def _now(self: JwtImpl) -> datetime:
        return datetime.now(tz=UTC)

    def _decode_typed_payload(
        self: JwtImpl,
        token: str,
        *,
        expected_type: str,
    ) -> dict[str, object] | None:
        try:
            data = _jwt_decode(
                token,
                self.cfg.secret,
                algorithms=[self.cfg.alg],
                audience=self.cfg.audience,
                issuer=self.cfg.issuer,
                options={"require": _REQUIRED_CLAIMS},
            )
        except (PyJWTError, TypeError):
            return None
        if data.get("typ") != expected_type:
            return None
        return data

    def issue_access(self: JwtImpl, *, user_id: UUID) -> str:
        now = self._now()
        payload = {
            "iss": self.cfg.issuer,
            "aud": self.cfg.audience,
            "sub": str(user_id),
            "typ": _ACCESS_KIND,
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + self.cfg.access_ttl).timestamp()),
        }
        return _jwt_encode(payload, self.cfg.secret, algorithm=self.cfg.alg)

    def issue_refresh(
        self: JwtImpl, *, user_id: UUID, fingerprint: str
    ) -> tuple[str, str]:
        now = self._now()
        jti = str(uuid4())
        payload = {
            "iss": self.cfg.issuer,
            "aud": self.cfg.audience,
            "sub": str(user_id),
            "typ": _REFRESH_KIND,
            "fpr": fingerprint,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int((now + self.cfg.refresh_ttl).timestamp()),
        }
        token = _jwt_encode(payload, self.cfg.secret, algorithm=self.cfg.alg)
        return token, jti

    def verify_access(self: JwtImpl, token: str) -> Result[UUID, AppError]:
        data = self._decode_typed_payload(token, expected_type=_ACCESS_KIND)
        if data is None:
            return _access_error()
        sub = data.get("sub")
        jti = data.get("jti")
        if not isinstance(sub, str) or not isinstance(jti, str) or not jti:
            return _access_error()
        try:
            return ResultImpl.ok(UUID(sub))
        except ValueError:
            return _access_error()

    def verify_refresh(
        self: JwtImpl, token: str
    ) -> Result[tuple[UUID, str, str], AppError]:
        data = self._decode_typed_payload(token, expected_type=_REFRESH_KIND)
        if data is None:
            return _refresh_error()
        sub = data.get("sub")
        fpr = data.get("fpr")
        jti = data.get("jti")
        if (
            not isinstance(sub, str)
            or not isinstance(fpr, str)
            or not fpr
            or not isinstance(jti, str)
            or not jti
        ):
            return _refresh_error()
        try:
            user_id = UUID(sub)
            return ResultImpl.ok(_refresh_payload(user_id, fpr, jti))
        except ValueError:
            return _refresh_error()
