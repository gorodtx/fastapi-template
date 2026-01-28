from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final
from uuid import UUID

from jwt import PyJWTError

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


if TYPE_CHECKING:

    def _jwt_encode_raw(
        payload: Mapping[str, object], key: str, *, algorithm: str
    ) -> str: ...

    def _jwt_decode_raw(
        token: str,
        key: str,
        *,
        algorithms: list[str],
        audience: str,
        issuer: str,
        options: dict[str, object],
    ) -> Mapping[str, object]: ...
else:
    from jwt import decode as _jwt_decode_raw
    from jwt import encode as _jwt_encode_raw


def _jwt_encode(
    payload: Mapping[str, object], key: str, *, algorithm: str
) -> str:
    return _jwt_encode_raw(payload, key, algorithm=algorithm)


def _jwt_decode(
    token: str,
    key: str,
    *,
    algorithms: list[str],
    audience: str,
    issuer: str,
    options: dict[str, object],
) -> dict[str, object]:
    data = _jwt_decode_raw(
        token,
        key,
        algorithms=algorithms,
        audience=audience,
        issuer=issuer,
        options=options,
    )
    out: dict[str, object] = {}
    for key_item, value in data.items():
        out[str(key_item)] = value
    return out


def _access_error(message: str) -> Result[UUID, AppError]:
    return ResultImpl.err_app(UnauthenticatedError(message))


def _refresh_error(message: str) -> Result[tuple[UUID, str], AppError]:
    return ResultImpl.err_app(UnauthenticatedError(message))


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

    def issue_access(self: JwtImpl, *, user_id: UUID) -> str:
        now = self._now()
        payload = {
            "iss": self.cfg.issuer,
            "aud": self.cfg.audience,
            "sub": str(user_id),
            "typ": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + self.cfg.access_ttl).timestamp()),
        }
        return _jwt_encode(payload, self.cfg.secret, algorithm=self.cfg.alg)

    def issue_refresh(
        self: JwtImpl, *, user_id: UUID, fingerprint: str
    ) -> str:
        now = self._now()
        payload = {
            "iss": self.cfg.issuer,
            "aud": self.cfg.audience,
            "sub": str(user_id),
            "typ": "refresh",
            "fpr": fingerprint,
            "iat": int(now.timestamp()),
            "exp": int((now + self.cfg.refresh_ttl).timestamp()),
        }
        return _jwt_encode(payload, self.cfg.secret, algorithm=self.cfg.alg)

    def verify_access(self: JwtImpl, token: str) -> Result[UUID, AppError]:
        try:
            data = _jwt_decode(
                token,
                self.cfg.secret,
                algorithms=[self.cfg.alg],
                audience=self.cfg.audience,
                issuer=self.cfg.issuer,
                options={"require": _REQUIRED_CLAIMS},
            )
        except PyJWTError as exc:
            return _access_error(f"Invalid access token: {exc}")

        if data.get("typ") != "access":
            return _access_error("Invalid access token type")
        sub = data.get("sub")
        if not isinstance(sub, str):
            return _access_error("Invalid token subject")
        try:
            return ResultImpl.ok(UUID(sub), AppError)
        except ValueError as exc:
            return _access_error(f"Invalid token subject: {exc}")

    def verify_refresh(
        self: JwtImpl, token: str
    ) -> Result[tuple[UUID, str], AppError]:
        try:
            data = _jwt_decode(
                token,
                self.cfg.secret,
                algorithms=[self.cfg.alg],
                audience=self.cfg.audience,
                issuer=self.cfg.issuer,
                options={"require": _REQUIRED_CLAIMS},
            )
        except PyJWTError as exc:
            return _refresh_error(f"Invalid refresh token: {exc}")

        if data.get("typ") != "refresh":
            return _refresh_error("Invalid refresh token type")
        sub = data.get("sub")
        fpr = data.get("fpr")
        if not isinstance(sub, str) or not isinstance(fpr, str) or not fpr:
            return _refresh_error("Invalid refresh token")
        try:
            fingerprint: str = fpr or ""
            return ResultImpl.ok((UUID(sub), fingerprint), AppError)
        except ValueError as exc:
            return _refresh_error(f"Invalid token subject: {exc}")
