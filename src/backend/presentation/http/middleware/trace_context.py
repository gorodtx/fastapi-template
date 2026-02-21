from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextvars import ContextVar, Token

from opentelemetry.trace import format_trace_id, get_current_span
from starlette.requests import Request
from starlette.responses import Response

_TRACE_ID_CTX: ContextVar[str | None] = ContextVar(
    "trace_id",
    default=None,
)


def get_trace_id() -> str | None:
    return _TRACE_ID_CTX.get()


async def trace_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    trace_id = _read_trace_id()
    token: Token[str | None] = _TRACE_ID_CTX.set(trace_id)
    try:
        response = await call_next(request)
        if trace_id is not None:
            response.headers["X-Trace-Id"] = trace_id
        return response
    finally:
        _TRACE_ID_CTX.reset(token)


def _read_trace_id() -> str | None:
    span = get_current_span()
    context = span.get_span_context()
    if not context.is_valid:
        return None
    return format_trace_id(context.trace_id)
