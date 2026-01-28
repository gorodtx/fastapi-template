from __future__ import annotations

from collections.abc import Awaitable

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
    RefreshStore,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import (
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
    refresh_store: RefreshStore

    async def __call__(
        self: LoginUserHandler,
        cmd: LoginUserCommand,
        /,
    ) -> Result[TokenPairDTO, AppError]:
        invalid_credentials = UnauthenticatedError("Invalid email or password")
        user_result = await self.gateway.users.get_by_email(cmd.email)
        if user_result.is_err():
            err = user_result.unwrap_err()
            if isinstance(err, NotFoundStorageError):
                return ResultImpl.err_app(invalid_credentials, TokenPairDTO)
            return ResultImpl.err_app(
                map_storage_error_to_app()(err), TokenPairDTO
            )

        user = user_result.unwrap()
        if not user.is_active:
            return ResultImpl.err_app(invalid_credentials, TokenPairDTO)

        def verify_password() -> Awaitable[bool]:
            return self.password_hasher.verify(
                cmd.raw_password, user.password.value
            )

        verify_result = await capture_async(
            verify_password, map_invalid_credentials()
        )
        if verify_result.is_err():
            return ResultImpl.err_from(verify_result)
        if not verify_result.unwrap():
            return ResultImpl.err_app(invalid_credentials, TokenPairDTO)

        user_id = user.id
        access_token = self.jwt_issuer.issue_access(user_id=user_id)
        refresh_token = self.jwt_issuer.issue_refresh(
            user_id=user_id,
            fingerprint=cmd.fingerprint,
        )

        def rotate_refresh() -> Awaitable[None]:
            return self.refresh_store.rotate(
                user_id=user_id,
                fingerprint=cmd.fingerprint,
                old="",
                new=refresh_token,
            )

        rotate_result = await capture_async(
            rotate_refresh, map_refresh_replay()
        )
        if rotate_result.is_err():
            return ResultImpl.err_from(rotate_result)

        return ResultImpl.ok(
            TokenPairDTO(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
            AppError,
        )
