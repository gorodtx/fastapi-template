from __future__ import annotations


class ApplicationError(Exception): ...


class ResourceNotFoundError(ApplicationError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"{resource} with identifier {identifier!r} not found")


class ConflictError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
