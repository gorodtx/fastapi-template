from __future__ import annotations

import uuid_utils.compat as uuid

from fastapi_backend.domain.core.entities.user import User
from fastapi_backend.domain.core.value_objects.email import Email
from fastapi_backend.domain.core.value_objects.login import Login
from fastapi_backend.domain.core.value_objects.password import Password
from fastapi_backend.domain.core.value_objects.username import Username
from fastapi_backend.domain.ports.event_dispatcher import EventDispatcherPort


class UserDomainService:
    def __init__(self, event_dispatcher: EventDispatcherPort) -> None:
        self._event_dispatcher = event_dispatcher

    def register_user(
        self, email: Email, login: Login, username: Username, password: Password
    ) -> User:
        user = User.register(
            id=uuid.uuid7(),
            email=email,
            login=login,
            username=username,
            password=password,
        )
        events = user.pull_events()
        self._event_dispatcher.publish(events)
        return user

    def change_user_email(self, user: User, new_email: Email) -> None:
        user.change_email(new_email)
        events = user.pull_events()
        self._event_dispatcher.publish(events)

    def change_user_username(self, user: User, new_username: Username) -> None:
        user.change_username(new_username)
        events = user.pull_events()
        self._event_dispatcher.publish(events)

    def change_user_password(self, user: User, new_password: Password) -> None:
        user.change_password(new_password)
        events = user.pull_events()
        self._event_dispatcher.publish(events)
