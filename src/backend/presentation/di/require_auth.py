from __future__ import annotations

from dishka.integrations.fastapi import FromDishka, inject

from backend.application.common.interfaces.auth.types import AuthUser


@inject
async def require_auth(_: FromDishka[AuthUser]) -> None:
    return None
