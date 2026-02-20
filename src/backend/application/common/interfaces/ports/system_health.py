from __future__ import annotations

from collections.abc import Awaitable
from typing import Protocol


class SystemHealthPort(Protocol):
    def is_db_alive(self: SystemHealthPort, /) -> Awaitable[bool]: ...

    def is_redis_alive(self: SystemHealthPort, /) -> Awaitable[bool]: ...
