from __future__ import annotations

import logging

import pytest

from backend.presentation.http.api.post_commit import run_best_effort


@pytest.mark.asyncio
async def test_run_best_effort_completes_successful_action() -> None:
    called = False

    async def action() -> None:
        nonlocal called
        called = True

    await run_best_effort(action(), effect="cache-invalidation")

    assert called is True


@pytest.mark.asyncio
async def test_run_best_effort_swallows_and_logs_errors(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def action() -> None:
        raise RuntimeError("boom")

    with caplog.at_level(logging.ERROR):
        await run_best_effort(action(), effect="cache-invalidation")

    assert any(
        "Post-commit side effect failed: cache-invalidation" in message
        for message in caplog.messages
    )
