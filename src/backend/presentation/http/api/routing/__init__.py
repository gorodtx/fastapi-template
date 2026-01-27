from __future__ import annotations

from fastapi import APIRouter

from backend.presentation.http.api.middlewere.auth import AuthzRoute
from backend.presentation.http.api.routing.auth import router as auth_router
from backend.presentation.http.api.routing.rbac import router as rbac_router
from backend.presentation.http.api.routing.users import router as users_router

api_router = APIRouter(route_class=AuthzRoute)
api_router.include_router(users_router)
api_router.include_router(rbac_router)
api_router.include_router(auth_router)

__all__ = ["api_router"]
