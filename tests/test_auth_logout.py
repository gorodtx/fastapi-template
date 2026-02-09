from __future__ import annotations

from dataclasses import dataclass

import pytest
from uuid_utils.compat import UUID

from backend.application.common.dtos.auth import SuccessDTO
from backend.application.common.exceptions.application import AppError
from backend.application.handlers.commands.auth.logout import (
    LogoutUserCommand,
    LogoutUserHandler,
)
from backend.application.handlers.result import Result, ResultImpl

_USER_ID = UUID("11111111-1111-1111-1111-111111111111")
_OTHER_USER_ID = UUID("22222222-2222-2222-2222-222222222222")


def _build_refresh_token() -> str:
    return "".join(("refresh", "-", "token"))


@dataclass(slots=True)
class _FakeJwtVerifier:
    user_id: UUID
    fingerprint: str
    jti: str = "jti-value"

    def verify_refresh(
        self: _FakeJwtVerifier, _token: str
    ) -> Result[tuple[UUID, str, str], AppError]:
        return ResultImpl.ok(
            (self.user_id, self.fingerprint, self.jti), AppError
        )


@dataclass(slots=True)
class _FakeRefreshTokens:
    revoked: tuple[UUID, str] | None = None

    async def revoke(
        self: _FakeRefreshTokens, *, user_id: UUID, fingerprint: str
    ) -> None:
        self.revoked = (user_id, fingerprint)


@pytest.mark.asyncio
async def test_logout_rejects_actor_and_refresh_subject_mismatch() -> None:
    refresh_tokens = _FakeRefreshTokens()
    handler = LogoutUserHandler(
        jwt_verifier=_FakeJwtVerifier(user_id=_USER_ID, fingerprint="fp"),
        refresh_tokens=refresh_tokens,
    )

    result = await handler(
        LogoutUserCommand(
            refresh_token=_build_refresh_token(),
            fingerprint="fp",
            actor_user_id=_OTHER_USER_ID,
        )
    )

    err = result.unwrap_err()
    assert err.code == "auth.unauthenticated"
    assert err.message == "Invalid refresh token"
    assert refresh_tokens.revoked is None


@pytest.mark.asyncio
async def test_logout_revoke_on_valid_actor_and_token() -> None:
    refresh_tokens = _FakeRefreshTokens()
    handler = LogoutUserHandler(
        jwt_verifier=_FakeJwtVerifier(user_id=_USER_ID, fingerprint="fp"),
        refresh_tokens=refresh_tokens,
    )

    result = await handler(
        LogoutUserCommand(
            refresh_token=_build_refresh_token(),
            fingerprint="fp",
            actor_user_id=_USER_ID,
        )
    )

    dto = result.unwrap()
    assert isinstance(dto, SuccessDTO)
    assert dto.success is True
    assert refresh_tokens.revoked == (_USER_ID, "fp")
