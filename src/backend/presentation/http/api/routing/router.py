from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from backend.presentation.di.require_auth import require_auth
from backend.presentation.http.api.routing.auth import router as auth_router
from backend.presentation.http.api.routing.rbac import router as rbac_router
from backend.presentation.http.api.routing.system import (
    router as system_router,
)
from backend.presentation.http.api.routing.users import router as users_router

protected_router: APIRouter = APIRouter(
    dependencies=[Depends(require_auth)],
    route_class=DishkaRoute,
)
protected_router.include_router(users_router)
protected_router.include_router(rbac_router)

api_router: APIRouter = APIRouter(route_class=DishkaRoute)
api_router.include_router(auth_router)
api_router.include_router(system_router)
api_router.include_router(protected_router)
