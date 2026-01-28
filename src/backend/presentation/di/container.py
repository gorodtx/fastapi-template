from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI

from backend.presentation.di.app_provider import AppProvider
from backend.presentation.di.request_provider import RequestProvider


class _EventRegistrar(Protocol):
    def add_event_handler(
        self: _EventRegistrar,
        event_type: str,
        func: Callable[[], Awaitable[None] | None],
    ) -> None: ...


def build_container() -> AsyncContainer:
    return make_async_container(
        AppProvider(), RequestProvider(), FastapiProvider()
    )


def setup_di(app: FastAPI) -> None:
    container = build_container()
    setup_dishka(container, app)

    async def _close_container() -> None:
        await container.close()

    _register_shutdown(app, _close_container)


def _register_shutdown(
    registrar: _EventRegistrar,
    func: Callable[[], Awaitable[None] | None],
) -> None:
    registrar.add_event_handler("shutdown", func)
