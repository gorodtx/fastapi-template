from __future__ import annotations

from functools import partial

import uuid_utils.compat as uuid

from backend.application.common.dtos.users import (
    UserCreateDTO,
    UserResponseDTO,
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
from backend.domain.core.services.users import build_user
from backend.domain.core.types.rbac import RoleCode
from backend.domain.ports.security.password_hasher import PasswordHasherPort


class CreateUserCommand(UserCreateDTO): ...


@handler(mode="write")
class CreateUserHandler(CommandHandler[CreateUserCommand, UserResponseDTO]):
    gateway: PersistenceGateway
    password_hasher: PasswordHasherPort
    default_registration_role: RoleCode

    async def __call__(
        self: CreateUserHandler, cmd: CreateUserCommand, /
    ) -> Result[UserResponseDTO, AppError]:
        return await run_result_in_tx(
            manager=self.gateway.manager,
            action_factory=lambda: self._execute(cmd),
        )

    async def _execute(
        self: CreateUserHandler, cmd: CreateUserCommand
    ) -> Result[UserResponseDTO, AppError]:
        hashed_result = await capture_async(
            partial(self.password_hasher.hash, cmd.raw_password),
            map_user_input_error(),
        )
        if isinstance(hashed_result, Err):
            return ResultImpl.err_from(hashed_result)
        hashed = hashed_result.value

        user_result = capture(
            lambda: build_user(
                id=uuid.uuid7(),
                email=cmd.email,
                login=cmd.login,
                username=cmd.username,
                password_hash=hashed,
            ),
            map_user_input_error(),
        )
        if isinstance(user_result, Err):
            return ResultImpl.err_from(user_result)
        user = user_result.value

        user.roles.add(self.default_registration_role)

        saved_user_result = (
            await self.gateway.users.save(user, include_roles=False)
        ).map_err(map_storage_error_to_app())
        if isinstance(saved_user_result, Err):
            return ResultImpl.err_from(saved_user_result)
        saved_user = saved_user_result.value

        replace_roles_result = (
            await self.gateway.rbac.replace_user_roles(
                user.id, {self.default_registration_role}
            )
        ).map_err(map_storage_error_to_app())
        if isinstance(replace_roles_result, Err):
            return ResultImpl.err_from(replace_roles_result)

        return ResultImpl.ok(present_user_response(saved_user))
