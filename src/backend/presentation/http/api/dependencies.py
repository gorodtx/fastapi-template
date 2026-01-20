from __future__ import annotations

from dataclasses import dataclass

from starlette.requests import Request

from backend.application.common.dtos.rbac import UserRolesResponseDTO
from backend.application.common.dtos.users import UserResponseDTO
from backend.application.handlers.base import CommandHandler, QueryHandler
from backend.application.handlers.commands.users.create import CreateUserCommand
from backend.application.handlers.queries.rbac.get_user_roles import GetUserRolesQuery
from backend.application.handlers.queries.users.get_user import GetUserQuery


@dataclass(slots=True)
class ApiHandlers:
    create_user: CommandHandler[CreateUserCommand, UserResponseDTO]
    get_user: QueryHandler[GetUserQuery, UserResponseDTO]
    get_user_roles: QueryHandler[GetUserRolesQuery, UserRolesResponseDTO]


def get_handlers(request: Request) -> ApiHandlers:
    handlers = getattr(request.app.state, "handlers", None)
    if not isinstance(handlers, ApiHandlers):
        raise RuntimeError("Handlers are not configured on application state")
    return handlers
