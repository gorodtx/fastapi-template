from __future__ import annotations

import importlib

__all__: list[str] = ["create_app"]


def __getattr__(name: str) -> object:
    if name == "create_app":
        return importlib.import_module("backend.startup").create_app
    raise AttributeError(name)
