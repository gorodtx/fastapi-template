from __future__ import annotations

from fastapi import FastAPI

from backend.presentation.app import create_app as _create_app


def create_app() -> FastAPI:
    return _create_app()
