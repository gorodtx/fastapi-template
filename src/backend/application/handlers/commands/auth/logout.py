from __future__ import annotations

from functools import partial

from backend.application.common.dtos.auth import LogoutUserDTO, SuccessDTO
from backend.application.common.exceptions.application import (
    AppError,
    UnauthenticatedError,
)
from backend.application.common.exceptions.error_mappers.auth import (
    map_invalid_refresh,
)
from backend.application.common.interfaces.auth.ports import (
    JwtVerifier,
)
from backend.application.common.tools.refresh_tokens import (
    RefreshTokenService,
)
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import (
    Err,
    Result,
    ResultImpl,
    capture_async,
)
from backend.application.handlers.transform import handler


class LogoutUserCommand(LogoutUserDTO): ...


@handler(mode="write")
class LogoutUserHandler(CommandHandler[LogoutUserCommand, SuccessDTO]):
    jwt_verifier: JwtVerifier
    refresh_tokens: RefreshTokenService

    async def __call__(
        self: LogoutUserHandler,
        cmd: LogoutUserCommand,
        /,
    ) -> Result[SuccessDTO, AppError]:
        verify_result = self.jwt_verifier.verify_refresh(cmd.refresh_token)
        if isinstance(verify_result, Err):
            return ResultImpl.err_from(verify_result)

        user_id, token_fingerprint, _token_jti = verify_result.value
        if user_id != cmd.actor_user_id:
            err = UnauthenticatedError("Invalid refresh token")
            return ResultImpl.err_app(err)
        if token_fingerprint != cmd.fingerprint:
            err = UnauthenticatedError("Refresh token fingerprint mismatch")
            return ResultImpl.err_app(err)

        revoke_result = await capture_async(
            partial(
                self.refresh_tokens.revoke,
                user_id=user_id,
                fingerprint=token_fingerprint,
            ),
            map_invalid_refresh(),
        )
        if isinstance(revoke_result, Err):
            return ResultImpl.err_from(revoke_result)

        return ResultImpl.ok(SuccessDTO())
