from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.presentation.di.require_auth import require_auth
from backend.presentation.http.api.routing.auth import router as auth_router
from backend.presentation.http.api.routing.rbac import router as rbac_router
from backend.presentation.http.api.routing.users import router as users_router

protected_router: APIRouter = APIRouter(
    dependencies=[Depends(require_auth)],
)
protected_router.include_router(users_router)
protected_router.include_router(rbac_router)

api_router: APIRouter = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(protected_router)

__all__: list[str] = ["api_router"]
