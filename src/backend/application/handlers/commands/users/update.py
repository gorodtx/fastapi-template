from __future__ import annotations

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
from backend.application.common.tools.tx_result import run_in_tx
from backend.application.handlers.base import CommandHandler
from backend.application.handlers.result import (
    Result,
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
        async def action() -> UserResponseDTO:
            user = (
                (
                    await self.gateway.users.get_by_id(
                        cmd.user_id,
                        include_roles=False,
                    )
                )
                .map_err(map_storage_error_to_app())
                .unwrap()
            )

            if cmd.email is not None:
                capture(
                    lambda: apply_user_patch(user, email=cmd.email),
                    map_user_input_error(),
                ).unwrap()

            if cmd.raw_password is not None:
                raw_password = cmd.raw_password
                hashed = (
                    await capture_async(
                        lambda: self.password_hasher.hash(raw_password),
                        map_user_input_error(),
                    )
                ).unwrap()
                capture(
                    lambda: apply_user_patch(user, password_hash=hashed),
                    map_user_input_error(),
                ).unwrap()

            saved_user = (
                (await self.gateway.users.save(user, include_roles=False))
                .map_err(map_storage_error_to_app())
                .unwrap()
            )

            return present_user_response(saved_user)

        return await run_in_tx(
            manager=self.gateway.manager,
            action=action,
            value_type=UserResponseDTO,
        )
