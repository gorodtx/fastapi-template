from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from backend.infrastructure.persistence.manager import TransactionManagerImpl


@dataclass(slots=True)
class _TxStub:
    session: _SessionStub
    nested: bool
    entered: bool = False
    exited: bool = False
    seen_exc: type[BaseException] | None = None

    async def __aenter__(self: _TxStub) -> _TxStub:
        self.entered = True
        self.session.in_tx = True
        return self

    async def __aexit__(
        self: _TxStub,
        exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: object,
    ) -> None:
        self.exited = True
        self.seen_exc = exc_type
        self.session.in_tx = False


@dataclass(slots=True)
class _SessionStub:
    in_tx: bool = False
    begin_calls: int = 0
    begin_nested_calls: int = 0
    commit_calls: int = 0
    rollback_calls: int = 0
    scopes: list[_TxStub] = field(default_factory=list)

    def in_transaction(self: _SessionStub) -> bool:
        return self.in_tx

    def begin(self: _SessionStub) -> _TxStub:
        self.begin_calls += 1
        scope = _TxStub(session=self, nested=False)
        self.scopes.append(scope)
        return scope

    def begin_nested(self: _SessionStub) -> _TxStub:
        self.begin_nested_calls += 1
        scope = _TxStub(session=self, nested=True)
        self.scopes.append(scope)
        return scope

    async def commit(self: _SessionStub) -> None:
        self.commit_calls += 1
        self.in_tx = False

    async def rollback(self: _SessionStub) -> None:
        self.rollback_calls += 1
        self.in_tx = False


@pytest.mark.asyncio
async def test_transaction_begins_and_exits_scope() -> None:
    session = _SessionStub()
    manager = TransactionManagerImpl(session)

    async with manager.transaction():
        assert session.begin_calls == 1
        assert session.commit_calls == 0
        assert session.rollback_calls == 0

    assert session.begin_calls == 1
    assert len(session.scopes) == 1
    assert session.scopes[0].entered is True
    assert session.scopes[0].exited is True
    assert session.scopes[0].seen_exc is None


@pytest.mark.asyncio
async def test_transaction_commits_current_active_transaction() -> None:
    session = _SessionStub(in_tx=True)
    manager = TransactionManagerImpl(session)

    async with manager.transaction():
        pass

    assert session.begin_calls == 0
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


@pytest.mark.asyncio
async def test_transaction_rolls_back_current_active_transaction_on_error() -> (
    None
):
    class _BoomError(Exception): ...

    session = _SessionStub(in_tx=True)
    manager = TransactionManagerImpl(session)

    with pytest.raises(_BoomError):
        async with manager.transaction():
            raise _BoomError()

    assert session.begin_calls == 0
    assert session.commit_calls == 0
    assert session.rollback_calls == 1


@pytest.mark.asyncio
async def test_transaction_is_noop_inside_existing_manager_scope() -> None:
    session = _SessionStub()
    manager = TransactionManagerImpl(session)

    async with manager.transaction(), manager.transaction():
        pass

    assert session.begin_calls == 1
    assert session.commit_calls == 0
    assert session.rollback_calls == 0
    assert len(session.scopes) == 1


@pytest.mark.asyncio
async def test_nested_transaction_requires_outer_scope() -> None:
    session = _SessionStub()
    manager = TransactionManagerImpl(session)

    with pytest.raises(RuntimeError):
        async with manager.transaction(nested=True):
            pass


@pytest.mark.asyncio
async def test_nested_transaction_uses_begin_nested_when_outer_exists() -> (
    None
):
    session = _SessionStub(in_tx=True)
    manager = TransactionManagerImpl(session)

    async with manager.transaction(nested=True):
        pass

    assert session.begin_nested_calls == 1
