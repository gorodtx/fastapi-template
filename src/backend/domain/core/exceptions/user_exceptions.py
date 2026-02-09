from __future__ import annotations

from src.backend.domain.core.exceptions.base import CorruptedInvariantError, DomainError
from src.backend.domain.core.value_objects.email import Email
from src.backend.domain.core.value_objects.user_id import UserId
from src.backend.domain.core.value_objects.username import Username


class UserAlreadyExistsError(DomainError):
    """User already exists - business rule violation."""

    ...


class UsernameAlreadyExistsError(UserAlreadyExistsError):
    def __init__(self, username: Username) -> None:
        super().__init__(f"Username {username.value!r} is already taken")


class EmailAlreadyExistsError(UserAlreadyExistsError):
    def __init__(self, email: Email) -> None:
        super().__init__(f"Email {email.value!r} is already registered")


class UserStateViolationError(DomainError):
    """User state transition violation."""

    ...


class UserAlreadyActiveError(UserStateViolationError):
    def __init__(self, username: Username) -> None:
        super().__init__(f"User {username.value!r} is already active")


class UserAlreadyInactiveError(UserStateViolationError):
    def __init__(self, username: Username) -> None:
        super().__init__(f"User {username.value!r} is already inactive")


class InactiveUserOperationError(UserStateViolationError):
    def __init__(self, username: Username, operation: str) -> None:
        super().__init__(f"Cannot perform {operation} on inactive user {username.value!r}")


class UserPermissionError(DomainError):
    """User lacks required permissions for operation."""

    ...


class InsufficientPermissionsError(UserPermissionError):
    def __init__(self, username: Username, required_permission: str) -> None:
        super().__init__(
            f"User {username.value!r} lacks required permission: {required_permission}"
        )


class RoleAssignmentNotAllowedError(UserPermissionError):
    def __init__(self, username: Username, role: str, reason: str) -> None:
        super().__init__(f"Cannot assign role {role!r} to user {username.value!r}: {reason}")


class SelfOperationNotAllowedError(UserPermissionError):
    def __init__(self, operation: str) -> None:
        super().__init__(f"User cannot perform {operation} on themselves")


class UserDataCorruptedError(CorruptedInvariantError):
    """Critical user data integrity violation."""

    def __init__(self, user_id: UserId, details: str) -> None:
        super().__init__(f"CRITICAL: User data corrupted for user {user_id.value!r}: {details}")


class DuplicateUserIdError(CorruptedInvariantError):
    """Critical error: multiple users found with same ID."""

    def __init__(self, user_id: UserId) -> None:
        super().__init__(f"CRITICAL: Multiple users found with same ID {user_id.value!r}")


class UserInvariantViolationError(CorruptedInvariantError):
    """Critical user business invariant violation."""

    def __init__(self, user_id: UserId, invariant: str) -> None:
        super().__init__(f"CRITICAL: User {user_id.value!r} invariant violated: {invariant}")
