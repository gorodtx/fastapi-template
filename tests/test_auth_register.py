from __future__ import annotations

from dataclasses import dataclass

import pytest
from uuid_utils.compat import UUID

from backend.application.common.dtos.users import UserResponseDTO
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.auth import RefreshTokenReplayError
from backend.application.handlers.result import ResultImpl
from backend.presentation.http.api.routing import auth as auth_routing
from backend.presentation.http.api.schemas.auth import RegisterRequest

_USER_ID: UUID = UUID("11111111-1111-1111-1111-111111111111")


def _build_raw_password() -> str:
    return "".join(("Strong", "Pass", "123", "!"))


def _build_token(prefix: str) -> str:
    return f"{prefix}-token-value"


@dataclass(slots=True)
class _FakeJwtIssuer:
    access_token: str
    refresh_token: str
    refresh_jti: str
    issued_access_for: UUID | None = None
    issued_refresh_for: tuple[UUID, str] | None = None

    def issue_access(self: _FakeJwtIssuer, *, user_id: UUID) -> str:
        self.issued_access_for = user_id
        return self.access_token

    def issue_refresh(
        self: _FakeJwtIssuer, *, user_id: UUID, fingerprint: str
    ) -> tuple[str, str]:
        self.issued_refresh_for = (user_id, fingerprint)
        return self.refresh_token, self.refresh_jti


@dataclass(slots=True)
class _FakeRefreshTokens:
    raised: Exception | None = None
    rotate_args: tuple[UUID, str, str, str] | None = None

    async def rotate(
        self: _FakeRefreshTokens,
        *,
        user_id: UUID,
        fingerprint: str,
        old_jti: str,
        new_jti: str,
    ) -> None:
        if self.raised is not None:
            raise self.raised
        self.rotate_args = (user_id, fingerprint, old_jti, new_jti)


@dataclass(slots=True)
class _DummyGateway:
    marker: str = "gateway"


@dataclass(slots=True)
class _DummyHasher:
    marker: str = "hasher"


@dataclass(slots=True)
class _TxScope:
    entered: bool = False
    exited: bool = False

    async def __aenter__(self: _TxScope) -> None:
        self.entered = True

    async def __aexit__(
        self: _TxScope,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: object,
    ) -> None:
        self.exited = True


@dataclass(slots=True)
class _SessionStub:
    tx: _TxScope

    def begin(self: _SessionStub) -> _TxScope:
        return self.tx


@pytest.mark.asyncio
async def test_register_user_creates_user_and_returns_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_cmd: dict[str, object] = {}
    raw_password = _build_raw_password()
    access_token = _build_token("access")
    refresh_token = _build_token("refresh")
    refresh_jti = "refresh-jti-value"

    class _FakeCreateUserHandler:
        def __init__(
            self: _FakeCreateUserHandler,
            *,
            gateway: object,
            password_hasher: object,
            default_registration_role: object,
        ) -> None:
            del gateway, password_hasher, default_registration_role

        async def __call__(
            self: _FakeCreateUserHandler, cmd: object
        ) -> object:
            captured_cmd["cmd"] = cmd
            return ResultImpl.ok(
                UserResponseDTO(
                    id=_USER_ID,
                    email="new@example.com",
                    login="newuser",
                    username="newuser",
                ),
                AppError,
            )

    monkeypatch.setattr(
        auth_routing, "CreateUserHandler", _FakeCreateUserHandler
    )

    payload = RegisterRequest(
        email="new@example.com",
        login="newuser",
        username="newuser",
        raw_password=raw_password,
        fingerprint="fp-test-1",
    )
    jwt_issuer = _FakeJwtIssuer(
        access_token=access_token,
        refresh_token=refresh_token,
        refresh_jti=refresh_jti,
    )
    refresh_tokens = _FakeRefreshTokens()
    session = _SessionStub(tx=_TxScope())

    response = await auth_routing.register_user(
        payload=payload,
        session=session,
        gateway=_DummyGateway(),
        password_hasher=_DummyHasher(),
        default_registration_role="user",
        jwt_issuer=jwt_issuer,
        refresh_tokens=refresh_tokens,
    )

    cmd = captured_cmd["cmd"]
    assert isinstance(cmd, auth_routing.CreateUserCommand)
    assert cmd.email == "new@example.com"
    assert cmd.login == "newuser"
    assert cmd.username == "newuser"
    assert cmd.raw_password == raw_password
    assert jwt_issuer.issued_access_for == _USER_ID
    assert jwt_issuer.issued_refresh_for == (_USER_ID, "fp-test-1")
    assert refresh_tokens.rotate_args == (
        _USER_ID,
        "fp-test-1",
        "",
        refresh_jti,
    )
    assert session.tx.entered is True
    assert session.tx.exited is True
    assert response.access_token == access_token
    assert response.refresh_token == refresh_token


@pytest.mark.asyncio
async def test_register_user_maps_refresh_replay_to_app_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_password = _build_raw_password()

    class _FakeCreateUserHandler:
        def __init__(
            self: _FakeCreateUserHandler,
            *,
            gateway: object,
            password_hasher: object,
            default_registration_role: object,
        ) -> None:
            del gateway, password_hasher, default_registration_role

        async def __call__(
            self: _FakeCreateUserHandler, cmd: object
        ) -> object:
            del cmd
            return ResultImpl.ok(
                UserResponseDTO(
                    id=_USER_ID,
                    email="new@example.com",
                    login="newuser",
                    username="newuser",
                ),
                AppError,
            )

    monkeypatch.setattr(
        auth_routing, "CreateUserHandler", _FakeCreateUserHandler
    )

    payload = RegisterRequest(
        email="new@example.com",
        login="newuser",
        username="newuser",
        raw_password=raw_password,
        fingerprint="fp-test-1",
    )
    session = _SessionStub(tx=_TxScope())

    with pytest.raises(AppError) as exc_info:
        await auth_routing.register_user(
            payload=payload,
            session=session,
            gateway=_DummyGateway(),
            password_hasher=_DummyHasher(),
            default_registration_role="user",
            jwt_issuer=_FakeJwtIssuer(
                access_token=_build_token("access"),
                refresh_token=_build_token("refresh"),
                refresh_jti="refresh-jti-value",
            ),
            refresh_tokens=_FakeRefreshTokens(
                raised=RefreshTokenReplayError("replay")
            ),
        )

    assert session.tx.entered is True
    assert session.tx.exited is True
    assert exc_info.value.code == "auth.unauthenticated"
    assert exc_info.value.message == "Refresh token replay detected"
