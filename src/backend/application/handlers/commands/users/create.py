from __future__ import annotations

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
from backend.application.common.tools.tx_result import run_in_tx
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import (
    Result,
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
        async def action() -> UserResponseDTO:
            hashed = (
                await capture_async(
                    lambda: self.password_hasher.hash(cmd.raw_password),
                    map_user_input_error(),
                )
            ).unwrap()
            user = capture(
                lambda: build_user(
                    id=uuid.uuid7(),
                    email=cmd.email,
                    login=cmd.login,
                    username=cmd.username,
                    password_hash=hashed,
                ),
                map_user_input_error(),
            ).unwrap()

            user.roles.add(self.default_registration_role)

            saved_user = (
                (await self.gateway.users.save(user, include_roles=False))
                .map_err(map_storage_error_to_app())
                .unwrap()
            )

            (
                await self.gateway.rbac.replace_user_roles(
                    user.id, {self.default_registration_role}
                )
            ).map_err(map_storage_error_to_app()).unwrap()

            return present_user_response(saved_user)

        return await run_in_tx(
            manager=self.gateway.manager,
            action=action,
            value_type=UserResponseDTO,
        )
