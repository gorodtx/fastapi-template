from __future__ import annotations


class RefreshTokenReplayError(PermissionError): ...


class InvalidRefreshTokenError(PermissionError): ...


class RefreshTokenLockTimeoutError(TimeoutError): ...
