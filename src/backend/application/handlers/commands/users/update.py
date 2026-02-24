from __future__ import annotations

from functools import partial

from backend.application.common.dtos.users import (
    UserResponseDTO,
    UserUpdateDTO,
)
from backend.application.common.exceptions.application import AppError
from backend.application.common.exceptions.error_mappers.storage import (
    map_storage_error_to_app,
)
from backend.application.common.exceptions.error_mappers.users import (
    map_user_input_error,
)
from backend.application.common.interfaces.ports.persistence.gateway import (
    PersistenceGateway,
)
from backend.application.common.presenters.users import present_user_response
from backend.application.common.tools.tx_result import run_result_in_tx
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import (
    Err,
    Result,
    ResultImpl,
    capture,
    capture_async,
)
from backend.application.handlers.transform import handler
from backend.domain.core.services.users import apply_user_patch
from backend.domain.ports.security.password_hasher import PasswordHasherPort


class UpdateUserCommand(UserUpdateDTO): ...


@handler(mode="write")
class UpdateUserHandler(CommandHandler[UpdateUserCommand, UserResponseDTO]):
    gateway: PersistenceGateway
    password_hasher: PasswordHasherPort

    async def __call__(
        self: UpdateUserHandler, cmd: UpdateUserCommand, /
    ) -> Result[UserResponseDTO, AppError]:
        return await run_result_in_tx(
            manager=self.gateway.manager,
            action_factory=lambda: self._execute(cmd),
        )

    async def _execute(
        self: UpdateUserHandler, cmd: UpdateUserCommand
    ) -> Result[UserResponseDTO, AppError]:
        user_result = (
            await self.gateway.users.get_by_id(
                cmd.user_id,
                include_roles=False,
            )
        ).map_err(map_storage_error_to_app())
        if isinstance(user_result, Err):
            return ResultImpl.err_from(user_result)
        user = user_result.value

        if cmd.email is not None:
            email_patch_result = capture(
                lambda: apply_user_patch(user, email=cmd.email),
                map_user_input_error(),
            )
            if isinstance(email_patch_result, Err):
                return ResultImpl.err_from(email_patch_result)

        raw_password = cmd.raw_password
        if raw_password is not None:
            hashed_result = await capture_async(
                partial(self.password_hasher.hash, raw_password),
                map_user_input_error(),
            )
            if isinstance(hashed_result, Err):
                return ResultImpl.err_from(hashed_result)
            hashed = hashed_result.value

            password_patch_result = capture(
                lambda: apply_user_patch(user, password_hash=hashed),
                map_user_input_error(),
            )
            if isinstance(password_patch_result, Err):
                return ResultImpl.err_from(password_patch_result)

        saved_user_result = (
            await self.gateway.users.save(user, include_roles=False)
        ).map_err(map_storage_error_to_app())
        if isinstance(saved_user_result, Err):
            return ResultImpl.err_from(saved_user_result)

        return ResultImpl.ok(present_user_response(saved_user_result.value))
