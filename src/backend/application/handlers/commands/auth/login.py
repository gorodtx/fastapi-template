from __future__ import annotations

from functools import partial

from backend.application.common.dtos.auth import LoginUserDTO, TokenPairDTO
from backend.application.common.exceptions.application import (
    AppError,
    UnauthenticatedError,
)
from backend.application.common.exceptions.error_mappers.auth import (
    map_invalid_credentials,
    map_refresh_replay,
)
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.exceptions.storage import NotFoundStorageError
from backend.application.common.interfaces.auth.ports import (
    JwtIssuer,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.tools.normalize_email import normalize_email
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
from backend.domain.ports.security.password_hasher import PasswordHasherPort


class LoginUserCommand(LoginUserDTO): ...


@handler(mode="write")
class LoginUserHandler(CommandHandler[LoginUserCommand, TokenPairDTO]):
    gateway: PersistenceGateway
    password_hasher: PasswordHasherPort
    jwt_issuer: JwtIssuer
    refresh_tokens: RefreshTokenService

    async def __call__(
        self: LoginUserHandler,
        cmd: LoginUserCommand,
        /,
    ) -> Result[TokenPairDTO, AppError]:
        invalid_credentials = UnauthenticatedError("Invalid email or password")
        normalized_email = normalize_email(cmd.email)
        user_result = await self.gateway.users.get_by_email(
            normalized_email,
            include_roles=False,
        )
        if isinstance(user_result, Err):
            err = user_result.error
            if isinstance(err, NotFoundStorageError):
                return ResultImpl.err_app(invalid_credentials)
            return ResultImpl.err_app(map_storage_error_to_app()(err))

        user = user_result.value
        if not user.is_active:
            return ResultImpl.err_app(invalid_credentials)

        verify_result = await capture_async(
            partial(
                self.password_hasher.verify,
                cmd.raw_password,
                user.password,
            ),
            map_invalid_credentials(),
        )
        if isinstance(verify_result, Err):
            return ResultImpl.err_from(verify_result)
        if not verify_result.value:
            return ResultImpl.err_app(invalid_credentials)

        user_id = user.id
        access_token = self.jwt_issuer.issue_access(user_id=user_id)
        refresh_token, refresh_jti = self.jwt_issuer.issue_refresh(
            user_id=user_id,
            fingerprint=cmd.fingerprint,
        )

        rotate_result = await capture_async(
            partial(
                self.refresh_tokens.rotate,
                user_id=user_id,
                fingerprint=cmd.fingerprint,
                old_jti="",
                new_jti=refresh_jti,
            ),
            map_refresh_replay(),
        )
        if isinstance(rotate_result, Err):
            return ResultImpl.err_from(rotate_result)

        return ResultImpl.ok(
            TokenPairDTO(
                access_token=access_token,
                refresh_token=refresh_token,
            )
        )
