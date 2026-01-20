from __future__ import annotations

from backend.application.common.interfaces.infra.persistence.gateway import PersistenceGateway
from backend.application.handlers.commands.users.create import CreateUserHandler
from backend.application.handlers.queries.rbac.get_user_roles import GetUserRolesHandler
from backend.application.handlers.queries.users.get_user import GetUserHandler
from backend.domain.ports.security.password_hasher import PasswordHasherPort
from backend.presentation.http.api.dependencies import ApiHandlers
from dishka import Provider, Scope, provide


class HandlersProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def handlers(
        self,
        gateway: PersistenceGateway,
        password_hasher: PasswordHasherPort,
    ) -> ApiHandlers:
        return ApiHandlers(
            create_user=CreateUserHandler(gateway=gateway, password_hasher=password_hasher),
            get_user=GetUserHandler(gateway=gateway),
            get_user_roles=GetUserRolesHandler(gateway=gateway),
        )
