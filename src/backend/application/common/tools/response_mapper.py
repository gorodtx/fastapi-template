from __future__ import annotations

from collections.abc import Callable


class ResponseMapper:
    __slots__ = ("_rules",)

    def __init__(self) -> None:
        self._rules: dict[
            tuple[type[object], type[object]],
            Callable[[object], object],
        ] = {}

    def register[S, D](
        self,
        src_type: type[S],
        dto_type: type[D],
        fn: Callable[[S], D],
    ) -> Callable[[S], D]:
        def _wrapper(value: object) -> object:
            if not isinstance(value, src_type):
                raise TypeError(f"Expected {src_type.__name__}, got {type(value).__name__}")
            return fn(value)

        self._rules[(src_type, dto_type)] = _wrapper
        return fn

    def present[D](self, src: object, dto_type: type[D]) -> D:
        key = (type(src), dto_type)
        if key not in self._rules:
            raise KeyError(f"No mapper registered for {type(src).__name__} -> {dto_type.__name__}")
        mapper = self._rules[key]
        result = mapper(src)
        if not isinstance(result, dto_type):
            raise TypeError(
                f"Mapper returned {type(result).__name__}, expected {dto_type.__name__}"
            )
        return result
