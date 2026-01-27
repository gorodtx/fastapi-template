from __future__ import annotations

from collections.abc import Awaitable

from backend.application.common.dtos.auth import RefreshUserDTO, TokenPairDTO
from backend.application.common.exceptions.application import AppError, UnauthenticatedError
from backend.application.common.exceptions.error_mappers.auth import map_refresh_replay
from backend.application.common.interfaces.auth.ports import JwtIssuer, JwtVerifier, RefreshStore
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import Result, ResultImpl, capture_async
from backend.application.handlers.transform import handler


class RefreshUserCommand(RefreshUserDTO): ...


@handler(mode="write")
class RefreshUserHandler(CommandHandler[RefreshUserCommand, TokenPairDTO]):
    jwt_verifier: JwtVerifier
    jwt_issuer: JwtIssuer
    refresh_store: RefreshStore

    async def __call__(
        self,
        cmd: RefreshUserCommand,
        /,
    ) -> Result[TokenPairDTO, AppError]:
        verify_result = self.jwt_verifier.verify_refresh(cmd.refresh_token)
        if verify_result.is_err():
            return ResultImpl.err_from(verify_result)

        user_id, token_fingerprint = verify_result.unwrap()
        if token_fingerprint != cmd.fingerprint:
            return ResultImpl.err(UnauthenticatedError("Refresh token fingerprint mismatch"))

        access_token = self.jwt_issuer.issue_access(user_id=user_id)
        refresh_token = self.jwt_issuer.issue_refresh(
            user_id=user_id,
            fingerprint=cmd.fingerprint,
        )

        def rotate_refresh() -> Awaitable[None]:
            return self.refresh_store.rotate(
                user_id=user_id,
                fingerprint=cmd.fingerprint,
                old=cmd.refresh_token,
                new=refresh_token,
            )

        rotate_result = await capture_async(rotate_refresh, map_refresh_replay())
        if rotate_result.is_err():
            return ResultImpl.err_from(rotate_result)

        return ResultImpl.ok(
            TokenPairDTO(
                access_token=access_token,
                refresh_token=refresh_token,
            )
        )
