from __future__ import annotations

from typing import TYPE_CHECKING

from backend.application.common.interfaces.auth.ports import Authenticator, JwtVerifier
from backend.application.common.interfaces.cache import StrCache
from backend.application.common.interfaces.infra.persistence.gateway import PersistenceGateway
from backend.presentation.http.api.dependencies import ApiHandlers
from dishka import Provider, Scope, provide

if TYPE_CHECKING:
    from backend.presentation.http.api import ApiDependencies


class ExternalDepsProvider(Provider):
    def __init__(self, deps: ApiDependencies) -> None:
        self._deps = deps

    @provide(scope=Scope.APP)
    def auth_gateway(self) -> PersistenceGateway:
        return self._deps.auth_gateway

    @provide(scope=Scope.APP)
    def auth_jwt_verifier(self) -> JwtVerifier:
        return self._deps.auth_jwt_verifier

    @provide(scope=Scope.APP)
    def auth_authenticator(self) -> Authenticator:
        return self._deps.auth_authenticator

    @provide(scope=Scope.APP)
    def auth_cache(self) -> StrCache:
        return self._deps.auth_cache

    @provide(scope=Scope.APP)
    def handlers(self) -> ApiHandlers:
        return self._deps.handlers


class AuthDepsProvider(Provider):
    def __init__(
        self,
        auth_gateway: PersistenceGateway,
        auth_jwt_verifier: JwtVerifier,
        auth_authenticator: Authenticator,
        auth_cache: StrCache,
    ) -> None:
        self._auth_gateway = auth_gateway
        self._auth_jwt_verifier = auth_jwt_verifier
        self._auth_authenticator = auth_authenticator
        self._auth_cache = auth_cache

    @provide(scope=Scope.APP)
    def auth_gateway(self) -> PersistenceGateway:
        return self._auth_gateway

    @provide(scope=Scope.APP)
    def auth_jwt_verifier(self) -> JwtVerifier:
        return self._auth_jwt_verifier

    @provide(scope=Scope.APP)
    def auth_authenticator(self) -> Authenticator:
        return self._auth_authenticator

    @provide(scope=Scope.APP)
    def auth_cache(self) -> StrCache:
        return self._auth_cache
