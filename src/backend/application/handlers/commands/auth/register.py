from __future__ import annotations

from backend.application.common.dtos.auth import (
    RegisterUserDTO,
    TokenPairDTO,
)
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.auth import (
    map_refresh_replay,
)
from backend.application.common.interfaces.auth.ports import JwtIssuer
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.tools.refresh_tokens import (
    RefreshTokenService,
)
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.commands.users.create import (
    CreateUserCommand,
    CreateUserHandler,
)
from backend.application.handlers.result import (
    Result,
    ResultImpl,
    capture_async,
)
from backend.application.handlers.transform import handler
from backend.domain.core.types.rbac import RoleCode
from backend.domain.ports.security.password_hasher import PasswordHasherPort


class RegisterUserCommand(RegisterUserDTO): ...


@handler(mode="write")
class RegisterUserHandler(CommandHandler[RegisterUserCommand, TokenPairDTO]):
    gateway: PersistenceGateway
    password_hasher: PasswordHasherPort
    default_registration_role: RoleCode
    jwt_issuer: JwtIssuer
    refresh_tokens: RefreshTokenService

    async def __call__(
        self: RegisterUserHandler,
        cmd: RegisterUserCommand,
        /,
    ) -> Result[TokenPairDTO, AppError]:
        create_handler = CreateUserHandler(
            gateway=self.gateway,
            password_hasher=self.password_hasher,
            default_registration_role=self.default_registration_role,
        )
        create_cmd = CreateUserCommand(
            email=cmd.email,
            login=cmd.login,
            username=cmd.username,
            raw_password=cmd.raw_password,
        )
        create_result = await create_handler(create_cmd)
        if create_result.is_err():
            return ResultImpl.err_from(create_result, TokenPairDTO)

        user = create_result.unwrap()
        access_token = self.jwt_issuer.issue_access(user_id=user.id)
        refresh_token, refresh_jti = self.jwt_issuer.issue_refresh(
            user_id=user.id,
            fingerprint=cmd.fingerprint,
        )
        rotate_result = await capture_async(
            lambda: self.refresh_tokens.rotate(
                user_id=user.id,
                fingerprint=cmd.fingerprint,
                old_jti="",
                new_jti=refresh_jti,
            ),
            map_refresh_replay(),
        )
        if rotate_result.is_err():
            return ResultImpl.err_from(rotate_result, TokenPairDTO)

        return ResultImpl.ok(
            TokenPairDTO(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
            AppError,
        )
