from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import TypeGuard

from backend.application.common.interfaces.auth.ports import Authenticator
from backend.application.common.interfaces.auth.types import (
    AuthUser,
    PermissionSpec,
)


def _is_mapping(value: object) -> TypeGuard[Mapping[object, object]]:
    return isinstance(value, Mapping)


def _is_iterable(value: object) -> TypeGuard[Iterable[object]]:
    return isinstance(value, Iterable) and not isinstance(
        value, (str, bytes, Mapping)
    )


def _empty_str_dict() -> dict[str, str]:
    return {}


@dataclass(slots=True)
class Context:
    authenticator: Authenticator
    user: AuthUser | None = None
    _keys: set[str] = field(default_factory=lambda: set[str]())
    request_id: str = ""
    request_method: str = ""
    request_path: str = ""
    request_url: str = ""
    request_path_params: dict[str, str] = field(
        default_factory=_empty_str_dict
    )
    request_query_params: dict[str, str] = field(
        default_factory=_empty_str_dict
    )
    request_json_params: object | None = None

    def set_user(self: Context, user: AuthUser | None) -> None:
        self.user = user

    def collect_keys(self: Context, data: object) -> None:
        if data is None:
            return
        if _is_mapping(data):
            for raw_key, raw_value in data.items():
                self._keys.add(str(raw_key))
                self.collect_keys(raw_value)
            return
        if _is_iterable(data):
            for raw_value in data:
                self.collect_keys(raw_value)
            return
        try:
            attrs: object = vars(data)
        except TypeError:
            attrs = None
        if _is_mapping(attrs):
            for raw_name in attrs:
                self._keys.add(str(raw_name))

    async def check_permission(self: Context, spec: PermissionSpec) -> None:
        if self.user is None:
            raise PermissionError("Unauthenticated")
        merged = PermissionSpec(
            code=spec.code,
            request_keys=frozenset(self._keys) | spec.request_keys,
            deny_fields=spec.deny_fields,
            allow_all_fields=spec.allow_all_fields,
        )
        perm = await self.authenticator.get_permission_for(
            self.user.id, merged
        )
        perm.check(merged)

    def request_keys(self: Context) -> frozenset[str]:
        return frozenset(self._keys)
