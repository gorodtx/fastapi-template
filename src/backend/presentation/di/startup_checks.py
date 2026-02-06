from __future__ import annotations

from fastapi import FastAPI
from fastapi.routing import APIRoute

from backend.presentation.di.require_auth import require_auth


def assert_closed_by_default(app: FastAPI) -> None:
    missing: list[str] = []
    public_prefixes = ("/auth", "/system")
    excluded_paths = {"/docs", "/redoc", "/openapi.json"}

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        path = route.path
        if path.startswith(public_prefixes) or path in excluded_paths:
            continue
        dependant = getattr(route, "dependant", None)
        if dependant is None:
            missing.append(path)
            continue
        if require_auth not in [dep.call for dep in dependant.dependencies]:
            missing.append(path)

    if missing:
        message = "Security policy violation: routes without require_auth:\n"
        message += "\n".join(sorted(missing))
        raise RuntimeError(message)
