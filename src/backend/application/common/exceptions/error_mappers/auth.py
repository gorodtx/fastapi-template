from __future__ import annotations

from collections.abc import Callable

from backend.application.common.exceptions.application import (
    AppError,
    ConflictError,
    UnauthenticatedError,
)
from backend.application.common.exceptions.auth import (
    InvalidRefreshTokenError,
    RefreshTokenLockTimeoutError,
    RefreshTokenReplayError,
)

type AuthRule = tuple[type[Exception], Callable[[Exception], AppError]]


def map_auth_error(*rules: AuthRule) -> Callable[[Exception], AppError]:
    def mapper(exc: Exception) -> AppError:
        for exc_type, factory in rules:
            if isinstance(exc, exc_type):
                return factory(exc)
        raise exc

    return mapper


def unauthenticated(message: str) -> Callable[[Exception], AppError]:
    def factory(_exc: Exception) -> AppError:
        return UnauthenticatedError(message)

    return factory


def conflict(message: str) -> Callable[[Exception], AppError]:
    def factory(_exc: Exception) -> AppError:
        return ConflictError(message)

    return factory


def map_invalid_credentials() -> Callable[[Exception], AppError]:
    return map_auth_error(
        (ValueError, unauthenticated("Invalid email or password"))
    )


def map_refresh_replay() -> Callable[[Exception], AppError]:
    return map_auth_error(
        (
            RefreshTokenReplayError,
            unauthenticated("Refresh token replay detected"),
        ),
        (
            RefreshTokenLockTimeoutError,
            conflict("Refresh token operation timeout, retry"),
        ),
    )


def map_invalid_refresh() -> Callable[[Exception], AppError]:
    return map_auth_error(
        (InvalidRefreshTokenError, unauthenticated("Invalid refresh token"))
    )


def map_refresh_token_error() -> Callable[[Exception], AppError]:
    return map_auth_error(
        (InvalidRefreshTokenError, unauthenticated("Invalid refresh token")),
        (
            RefreshTokenReplayError,
            unauthenticated("Refresh token replay detected"),
        ),
        (
            RefreshTokenLockTimeoutError,
            conflict("Refresh token operation timeout, retry"),
        ),
    )
