from __future__ import annotations

from uuid_utils.compat import UUID

from backend.domain.core.exceptions.base import CorruptedInvariantError, DomainError
from backend.domain.core.value_objects.identity.email import Email
from backend.domain.core.value_objects.identity.username import Username


class UserAlreadyExistsError(DomainError):
    """User already exists - business rule violation."""

    __slots__ = ()


class UsernameAlreadyExistsError(UserAlreadyExistsError):
    __slots__ = ("_username",)

    def __init__(self, username: Username) -> None:
        self._username = username
        super().__init__(f"Username {username.value!r} is already taken")


class EmailAlreadyExistsError(UserAlreadyExistsError):
    __slots__ = ("_email",)

    def __init__(self, email: Email) -> None:
        self._email = email
        super().__init__(f"Email {email.value!r} is already registered")


class UserStateViolationError(DomainError):
    """User state transition violation."""

    __slots__ = ()


class UserAlreadyActiveError(UserStateViolationError):
    __slots__ = ("_username",)

    def __init__(self, username: Username) -> None:
        self._username = username
        super().__init__(f"User {username.value!r} is already active")


class UserAlreadyInactiveError(UserStateViolationError):
    __slots__ = ("_username",)

    def __init__(self, username: Username) -> None:
        self._username = username
        super().__init__(f"User {username.value!r} is already inactive")


class InactiveUserOperationError(UserStateViolationError):
    __slots__ = ("_operation", "_username")

    def __init__(self, username: Username, operation: str) -> None:
        self._username = username
        self._operation = operation
        super().__init__(f"Cannot perform {operation} on inactive user {username.value!r}")


class UserPermissionError(DomainError):
    """User lacks required permissions for operation."""

    __slots__ = ()


class InsufficientPermissionsError(UserPermissionError):
    __slots__ = ("_required_permission", "_username")

    def __init__(self, username: Username, required_permission: str) -> None:
        self._username = username
        self._required_permission = required_permission
        super().__init__(
            f"User {username.value!r} lacks required permission: {required_permission}"
        )


class RoleAssignmentNotAllowedError(UserPermissionError):
    __slots__ = ("_reason", "_role", "_username")

    def __init__(self, username: Username, role: str, reason: str) -> None:
        self._username = username
        self._role = role
        self._reason = reason
        super().__init__(f"Cannot assign role {role!r} to user {username.value!r}: {reason}")


class SelfOperationNotAllowedError(UserPermissionError):
    __slots__ = ("_operation",)

    def __init__(self, operation: str) -> None:
        self._operation = operation
        super().__init__(f"User cannot perform {operation} on themselves")


class UserDataCorruptedError(CorruptedInvariantError):
    """Critical user data integrity violation."""

    __slots__ = ("_details", "_user_id")

    def __init__(self, user_id: UUID, details: str) -> None:
        self._user_id = user_id
        self._details = details
        super().__init__(f"CRITICAL: User data corrupted for user {user_id!s}: {details}")


class DuplicateUserIdError(CorruptedInvariantError):
    """Critical error: multiple users found with same ID."""

    __slots__ = ("_user_id",)

    def __init__(self, user_id: UUID) -> None:
        self._user_id = user_id
        super().__init__(f"CRITICAL: Multiple users found with same ID {user_id!s}")


class UserInvariantViolationError(CorruptedInvariantError):
    """Critical user business invariant violation."""

    __slots__ = ("_invariant", "_user_id")

    def __init__(self, user_id: UUID, invariant: str) -> None:
        self._user_id = user_id
        self._invariant = invariant
        super().__init__(f"CRITICAL: User {user_id!s} invariant violated: {invariant}")
