from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import NoReturn

from backend.application.common.exceptions.application import AppError

type Result[T, E: Exception] = Ok[T, E] | Err[T, E]


@dataclass(frozen=True, slots=True)
class Ok[T, E: Exception]:
    value: T

    def is_ok(self: Ok[T, E]) -> bool:
        return True

    def is_err(self: Ok[T, E]) -> bool:
        return False

    def unwrap(self: Ok[T, E]) -> T:
        return self.value

    def unwrap_err(self: Ok[T, E]) -> NoReturn:
        raise RuntimeError("Result has no error")

    def unwrap_or(self: Ok[T, E], _default: T) -> T:
        return self.value

    def unwrap_or_raise(self: Ok[T, E], _err: Exception) -> T:
        return self.value

    def map[U](self: Ok[T, E], fn: Callable[[T], U]) -> Result[U, E]:
        return Ok(fn(self.value))

    def map_err[F: Exception](
        self: Ok[T, E], _fn: Callable[[E], F]
    ) -> Result[T, F]:
        return Ok(self.value)

    def and_then[U](
        self: Ok[T, E], fn: Callable[[T], Result[U, E]]
    ) -> Result[U, E]:
        return fn(self.value)


@dataclass(frozen=True, slots=True)
class Err[T, E: Exception]:
    error: E

    def is_ok(self: Err[T, E]) -> bool:
        return False

    def is_err(self: Err[T, E]) -> bool:
        return True

    def unwrap(self: Err[T, E]) -> NoReturn:
        raise self.error

    def unwrap_err(self: Err[T, E]) -> E:
        return self.error

    def unwrap_or_raise(self: Err[T, E], err: Exception) -> NoReturn:
        raise err from self.error

    def map[U](self: Err[T, E], _fn: Callable[[T], U]) -> Result[U, E]:
        return Err(self.error)

    def map_err[F: Exception](
        self: Err[T, E], fn: Callable[[E], F]
    ) -> Result[T, F]:
        return Err(fn(self.error))

    def and_then[U](
        self: Err[T, E], _fn: Callable[[T], Result[U, E]]
    ) -> Result[U, E]:
        return Err(self.error)


class ResultImpl:
    @staticmethod
    def ok[T, E: Exception](
        value: T, _error_type: type[E] | None = None
    ) -> Ok[T, E]:
        return Ok(value)

    @staticmethod
    def err[T, E: Exception](
        error: E, _value_type: type[T] | None = None
    ) -> Err[T, E]:
        return Err(error)

    @staticmethod
    def err_app[T](
        error: AppError, _value_type: type[T] | None = None
    ) -> Err[T, AppError]:
        return Err(error)

    @staticmethod
    def err_from[T, U, E: Exception](
        other: Result[U, E], _value_type: type[T] | None = None
    ) -> Err[T, E]:
        return Err(other.unwrap_err())


def capture[T, E: Exception](
    fn: Callable[[], T],
    map_exc: Callable[[Exception], E],
) -> Result[T, E]:
    try:
        return ResultImpl.ok(fn())
    except Exception as exc:
        return ResultImpl.err(map_exc(exc))


async def capture_async[T, E: Exception](
    fn: Callable[[], Awaitable[T]],
    map_exc: Callable[[Exception], E],
) -> Result[T, E]:
    try:
        return ResultImpl.ok(await fn())
    except Exception as exc:
        return ResultImpl.err(map_exc(exc))
